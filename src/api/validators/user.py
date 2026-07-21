from typing import Optional, Union
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.user import user_crud
from models import User, UserRole
from schemas.user import UserCreate, UserUpdate

from core.constants import (
    UNIQUE_USER_FIELDS,
    UNIQUE_USER_FIELD_ERRORS,
    USER_CONTACT_REQUIRED_ERROR,
    USER_UPDATE_RULES,
)


class UserValidator:
    """Валидатор для пользователей."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация валидатора."""
        self.session = session
        self.crud = user_crud

    async def check_login_exists(self, user_data: UserCreate) -> None:
        """Проверка, что у пользователя есть email или phone."""
        if user_data.email is None and user_data.phone is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=USER_CONTACT_REQUIRED_ERROR,
            )

    async def check_login_after_update(self, user_data: UserUpdate, user: User) -> None:
        """Проверка, что после обновления у пользователя останется email или phone."""
        update_data = user_data.model_dump(exclude_unset=True)
        email = update_data.get('email', user.email)
        phone = update_data.get('phone', user.phone)

        if email is None and phone is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=USER_CONTACT_REQUIRED_ERROR,
            )

    async def check_unique_fields(
        self,
        user_data: Union[UserCreate, UserUpdate],
        user_id: Optional[UUID] = None,
    ) -> None:
        """Проверка уникальности полей пользователя."""
        for field in UNIQUE_USER_FIELDS:
            value = getattr(user_data, field, None)
            if value is None:
                continue

            existing_user = await self.crud.get_by_attributes(self.session, **{field: value})

            if existing_user is not None and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=UNIQUE_USER_FIELD_ERRORS[field],
                )

    async def check_permission_for_update_user(
        self,
        update_data: UserUpdate,
        current_user: User,
        target_user: User,
    ) -> None:
        """Проверка прав на изменение роли пользователя и статуса активности.

        Разрешено только администраторам.
        Администратор не может изменить свою роль или поменять свой статус.
        """
        for field, rules in USER_UPDATE_RULES.items():
            field_value = getattr(update_data, field, None)
            if field_value is None:
                continue

            if current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=rules['no_permission_error'],
                )

            if target_user.id == current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=rules['self_action_error'],
                )
