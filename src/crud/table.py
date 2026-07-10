from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models import Table
from schemas.table import TableCreate, TableUpdate


class CRUDTable(CRUDBase[Table, TableCreate, TableUpdate]):
    """CRUD для модели Table."""

    async def create(
        self,
        obj_in: TableCreate,
        cafe_id: UUID,
        session: AsyncSession,
    ) -> Table:
        """Создать стол в кафе."""
        data = obj_in.model_dump(exclude_unset=True)
        data['cafe_id'] = cafe_id
        db_obj = self.model(**data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj


table_crud = CRUDTable(Table)
