from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud import cafe_crud
from models import User, UserRole
from schemas.cafe import CafeUpdate

from core.constants import CAFE_STATUS_CHANGE_ERROR, CAFE_UNIQUE_CONSTRAINT_ERROR


class CafeValidator:
    """Валидатор для кафе."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация валидатора."""
        self.session = session
        self.crud = cafe_crud

    async def check_unique_constraint(
        self,
        name: str,
        address: str,
        phone: str,
        exclude_id: Optional[UUID] = None,
    ) -> None:
        """Проверка, существует ли кафе с переданными названием, адресом и номером телефона."""
        cafe = await self.crud.get_unique_cafe(name, address, phone, self.session, exclude_id)
        if cafe is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=CAFE_UNIQUE_CONSTRAINT_ERROR,
            )

    async def check_update_permission(
        self,
        update_data: CafeUpdate,
        current_user: User,
    ) -> None:
        """Проверка прав на обновление поля is_active (мягкое удаление)."""
        if update_data.is_active is not None and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=CAFE_STATUS_CHANGE_ERROR,
            )
