from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models import Cafe, User
from schemas.cafe import CafeCreate, CafeUpdate


class CRUDCafe(CRUDBase[Cafe, CafeCreate, CafeUpdate]):
    """CRUD для модели Cafe."""

    async def create(
        self,
        obj_in: CafeCreate,
        session: AsyncSession,
    ) -> Cafe:
        """Создать новое кафе с привязкой менеджеров."""
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        managers_id = obj_in_data.pop('managers_id', None)

        db_obj = self.model(**obj_in_data)
        if managers_id:
            managers = await session.execute(
                select(User).where(User.id.in_(managers_id)),
            )
            db_obj.managers = managers.scalars().all()

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: Cafe,
        obj_in: CafeUpdate,
        session: AsyncSession,
    ) -> Cafe:
        """Обновить кафе с возможностью обновления списка менеджеров."""
        obj_data = obj_in.model_dump(exclude_unset=True)
        managers_id = obj_data.pop('managers_id', None)

        for key, value in obj_data.items():
            setattr(db_obj, key, value)

        if managers_id is not None:
            if managers_id:
                managers = await session.execute(
                    select(User).where(User.id.in_(managers_id)),
                )
                db_obj.managers = managers.scalars().all()
            else:
                db_obj.managers = []

        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def get_unique_cafe(
        self,
        name: str,
        address: str,
        phone: str,
        session: AsyncSession,
        exclude_id: Optional[UUID] = None,
    ) -> Optional[Cafe]:
        """Получить кафе с комбинацией полей (название, адрес, номер телефона)."""
        query = select(Cafe).where(
            Cafe.name == name,
            Cafe.address == address,
            Cafe.phone == phone,
        )

        if exclude_id is not None:
            query = query.where(Cafe.id != exclude_id)
        obj = await session.execute(query)
        return obj.scalar()


cafe_crud = CRUDCafe(Cafe)
