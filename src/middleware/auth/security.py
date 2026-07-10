from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User

from .password import validate_login, verify_password
from core.config import settings
from core.constants import (
    EXPIRED_TOKEN_ERROR,
    INVALID_TOKEN_ERROR,
    JWT_SUB_FIELD,
    TOKEN_LIFE_HOURS,
    TOKEN_TYPE,
)


def make_not_authenticated_error(detail: str) -> HTTPException:
    """Создаёт HTTP исключение для неавторизованного доступа."""
    return HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail=detail,
        headers={'WWW-Authenticate': TOKEN_TYPE},
    )


def parse_auth_header(auth_header: str) -> str:
    """Парсит заголовок Authorization и возвращает токен."""
    parts = auth_header.split()

    if len(parts) != 2 or parts[0].lower() != TOKEN_TYPE.lower():
        raise make_not_authenticated_error(INVALID_TOKEN_ERROR)

    return parts[1]


def decode_token(token: str) -> dict:
    """Декодирует JWT токен."""
    try:
        return jwt.decode(
            token=token,
            key=settings.secret,
            algorithms=[settings.algorithm],
        )
    except ExpiredSignatureError as exc:
        raise make_not_authenticated_error(EXPIRED_TOKEN_ERROR) from exc
    except JWTError as exc:
        raise make_not_authenticated_error(INVALID_TOKEN_ERROR) from exc


def get_user_id_from_token(token: str) -> UUID:
    """Извлекает user_id (UUID) из токена."""
    payload = decode_token(token)
    raw_user_id = payload.get(JWT_SUB_FIELD)

    if not raw_user_id:
        raise make_not_authenticated_error(INVALID_TOKEN_ERROR)

    try:
        return UUID(raw_user_id)
    except ValueError as exc:
        raise make_not_authenticated_error(INVALID_TOKEN_ERROR) from exc


def validate_token_and_get_user_id(auth_header: str) -> Tuple[Optional[UUID], Optional[HTTPException]]:
    """Валидирует токен и возвращает user_id или ошибку."""
    try:
        token = parse_auth_header(auth_header)
        user_id = get_user_id_from_token(token)
        return user_id, None
    except HTTPException as error:
        return None, error


def create_access_token(data: dict) -> str:
    """Процесс генерации JWT токена."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_LIFE_HOURS)
    to_encode.update({'exp': expire})
    return jwt.encode(
        to_encode,
        key=settings.secret,
        algorithm=settings.algorithm,
    )


class AuthService:
    """Сервис класс для процесса аутентификации."""

    @staticmethod
    async def authenticate_user(
        session: AsyncSession,
        login: str,
        password: str,
    ) -> Optional[User]:
        """Ауентификация пользователя через его логин."""
        try:
            confirmed_login = validate_login(login)
        except ValueError:
            return None

        # Ищем пользователя
        query = select(User).where(
            or_(
                User.email == confirmed_login,
                User.phone == confirmed_login,
            ),
        )
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        # Проверяем пароль
        if not user or not verify_password(password, user.password):
            return None

        return user


auth_service = AuthService()
