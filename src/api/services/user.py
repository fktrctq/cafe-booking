from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.base import BaseService
from api.validators.user import UserValidator
from cache.cleaner_cache import cache_cleaner_client
from crud import user_crud
from models import User
from schemas.user import UserCreate, UserUpdate

from core.cache_conf import cache_settings
from core.db import SessionDep


class UserService(BaseService[User, UserCreate, UserUpdate]):
    """Сервис для работы с пользователями."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация сервиса."""
        super().__init__(user_crud, session)
        self.validator = UserValidator(session)

    async def clean_cache(self, user_id: UUID = None, new: bool = False) -> None:
        """Удаление ключей кеша связанных с пользователем."""
        if user_id:
            await cache_cleaner_client.delete_key_swr_background(
                f'{cache_settings.auth_key}:{user_id}',
            )
            await cache_cleaner_client.delete_key_by_tag_background(
                f'{cache_settings.user_tag}:{user_id}',
            )
        elif new:
            await cache_cleaner_client.delete_key_by_tag_background(
                cache_settings.user_list_tag,
            )
        else:
            return

    async def get_all_users(self) -> list[User]:
        """Получение всех пользователей."""
        return await self.crud.get_all(self.session)

    async def get_user_or_404(self, user_id: UUID) -> User:
        """Получение пользователя по ID с проверкой существования."""
        return await self.get_object_or_404(user_id)

    async def create_user(self, user_data: UserCreate) -> User:
        """Создание нового пользователя."""
        await self.validator.check_login_exists(user_data)
        await self.validator.check_unique_fields(user_data)
        await self.clean_cache(new=True)
        return await self.crud.create(user_data, self.session)

    async def update_current_user(
        self,
        user_data: UserUpdate,
        current_user: User,
    ) -> User:
        """Обновление профиля текущего пользователя."""
        await self.validator.check_permission_for_update_user(user_data, current_user, current_user)
        await self.validator.check_login_after_update(user_data, current_user)
        await self.validator.check_unique_fields(user_data, current_user.id)
        # Присоединяем объект пользователя к текущей сессии, т.к. обект из AuthMiddleware а там своя сессия
        current_user = await self.session.merge(current_user)
        current_user = await self.crud.update(current_user, user_data, self.session)
        await self.clean_cache(current_user.id)
        return current_user

    async def update_user_by_id(
        self,
        user_id: UUID,
        user_data: UserUpdate,
        current_user: User,
    ) -> User:
        """Обновление пользователя по ID."""
        target_user = await self.get_user_or_404(user_id)
        await self.validator.check_permission_for_update_user(user_data, current_user, target_user)
        await self.validator.check_login_after_update(user_data, target_user)
        await self.validator.check_unique_fields(user_data, user_id)
        await self.clean_cache(user_id)
        return await self.crud.update(target_user, user_data, self.session)


async def get_user_service(session: SessionDep) -> UserService:
    """DI для сервиса пользователей."""
    return UserService(session)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
