from datetime import time
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models import Slot
from schemas.slot import SlotCreate, SlotUpdate


class CRUDSlot(CRUDBase[Slot, SlotCreate, SlotUpdate]):
    """CRUD для модели Slot."""

    async def create(
        self,
        obj_in: SlotCreate,
        cafe_id: UUID,
        session: AsyncSession,
    ) -> Slot:
        """Создать временной слот в кафе."""
        data = obj_in.model_dump(exclude_unset=True)
        data['cafe_id'] = cafe_id
        db_obj = self.model(**data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def get_slot_by_time(
        self,
        cafe_id: UUID,
        start_time: time,
        end_time: time,
        session: AsyncSession,
        exclude_id: Optional[UUID] = None,
    ) -> Optional[Slot]:
        """Получить слот по времени в конкретном кафе."""
        query = select(Slot).where(
            Slot.cafe_id == cafe_id,
            Slot.start_time == start_time,
            Slot.end_time == end_time,
        )
        if exclude_id is not None:
            query = query.where(Slot.id != exclude_id)

        result = await session.execute(query)
        return result.scalar()

    async def get_slots_by_ids(
        self,
        session: AsyncSession,
        slot_ids: list[UUID],
    ) -> list[Slot]:
        """Получить слоты по списку ID."""
        result = await session.execute(select(Slot).where(Slot.id.in_(slot_ids)))
        return result.scalars().all()


slot_crud = CRUDSlot(Slot)
