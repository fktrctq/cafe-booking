import logging
from http import HTTPStatus
from typing import Any, Optional

from fastapi import HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from starlette.types import ASGIApp

from cache.swr_cache import swr_cache_redis
from crud.user import user_crud
from models.user import User
from schemas.user import UserResponse

from .security import make_not_authenticated_error, validate_token_and_get_user_id
from core.cache_conf import cache_settings
from core.constants import (
    INTERNAL_DB_ERROR,
    USER_NOT_FOUND_ERROR,
)
from core.db import AsyncSessionLocal

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware аутентификации."""

    def __init__(self, app: ASGIApp, dispatch: DispatchFunction | None = None) -> None:
        """Инициализация middleware аутентификации."""
        super().__init__(app, dispatch)

    def _restore_user_from_cache(self, user_data: Any) -> Optional[User]:
        """Восстановление ORM модели User из данных кеша."""
        try:
            if user_data is None:
                return None

            if isinstance(user_data, User):
                return user_data

            if isinstance(user_data, UserResponse):
                return User(**user_data.model_dump())

        except (ValueError, TypeError) as error:
            logger.error(
                f'Ошибка при восстановлении объекта User из кеша: {error}',
                exc_info=True,
            )
            return None

    async def get_user(self, user_id: Any) -> Optional[User]:
        """Получение объекта пользователя."""
        async with AsyncSessionLocal() as session:
            try:
                user = await user_crud.get(user_id, session)
                if not user:
                    raise make_not_authenticated_error(USER_NOT_FOUND_ERROR)
                session.expunge(user)  # Открепляем обект от сессии
                return user
            except SQLAlchemyError as error:
                logger.error(
                    f'Ошибка БД при получении пользователя user_id={user_id}: {error}',
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail=INTERNAL_DB_ERROR,
                )

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Обработка запроса с аутентификацией и валидацией токена."""
        auth_header = request.headers.get('Authorization')
        if auth_header is None:
            request.state.user = None
            return await call_next(request)

        user_id, error = validate_token_and_get_user_id(auth_header)
        if error:
            logger.error(f'Ошибка валидации токена : {error.detail}')
            return Response(
                content=f'{{"detail": "{error.detail}"}}',
                status_code=error.status_code,
                media_type='application/json',
            )
        if cache_settings.auth_cache:
            user_data = await swr_cache_redis.get_or_update(
                cache_key=f'{cache_settings.auth_key}:{user_id}',
                func=lambda: self.get_user(user_id),
                ttl=cache_settings.auth_ttl,
                stale_ttl=cache_settings.auth_stale_ttl,
                response_model=UserResponse,
            )
            user = self._restore_user_from_cache(user_data)
            if user is None:
                logger.warning(f'Пользователь с ID: {user_id} не найден!!!')
                raise make_not_authenticated_error(USER_NOT_FOUND_ERROR)
            request.state.user = user

        else:
            request.state.user = await self.get_user(user_id)

        return await call_next(request)
