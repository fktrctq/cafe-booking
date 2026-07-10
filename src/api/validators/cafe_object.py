from datetime import time
from typing import Optional, Union
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud import slot_crud
from models import Slot, Table

from core.constants import OBJECT_NOT_BELONG_TO_CAFE_ERROR, SLOT_ALREADY_EXISTS_ERROR


class CafeObjectValidator:
    """Общий валидатор для объектов, принадлежащих кафе."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация валидатора."""
        self.session = session

    async def check_object_belongs_to_cafe(
        self,
        obj: Union[Slot, Table],
        cafe_id: UUID,
    ) -> Union[Slot, Table]:
        """Проверка принадлежности объекта к кафе."""
        if obj.cafe_id != cafe_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=OBJECT_NOT_BELONG_TO_CAFE_ERROR,
            )
        return obj


class SlotValidator(CafeObjectValidator):
    """Валидатор для временных слотов кафе."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация валидатора."""
        super().__init__(session)
        self.crud = slot_crud

    async def check_unique_slot(
        self,
        cafe_id: UUID,
        start_time: time,
        end_time: time,
        exclude_id: Optional[UUID] = None,
    ) -> None:
        """Проверка, что слот с таким временем не существует в кафе."""
        existing_slot = await self.crud.get_slot_by_time(
            cafe_id,
            start_time,
            end_time,
            self.session,
            exclude_id,
        )
        if existing_slot is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=SLOT_ALREADY_EXISTS_ERROR,
            )
