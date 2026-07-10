from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.services import CafeServiceDep
from api.services.base_cafe_object import BaseCafeObjectService
from cache.cleaner_cache import cache_cleaner_client
from crud import table_crud
from models import Table, User
from schemas.table import TableCreate, TableUpdate

from core.cache_conf import cache_settings
from core.db import SessionDep


class TableService(BaseCafeObjectService[Table, TableCreate, TableUpdate]):
    """Сервис для работы со столами кафе."""

    def __init__(self, session: AsyncSession, cafe_service: CafeServiceDep) -> None:
        """Инициализация сервиса."""
        super().__init__(table_crud, session, cafe_service)

    async def clean_cache(self, table_id: UUID = None, new: bool = False) -> None:
        """Удаление ключей кеша по тегу."""
        if new:
            tag = cache_settings.table_list_tag
        if table_id:
            tag = f'{cache_settings.table_tag}:{table_id}'
        else:
            return
        await cache_cleaner_client.delete_key_by_tag_background(tag)

    async def create_object_in_cafe(
        self,
        cafe_id: UUID,
        obj_data: TableCreate,
        current_user: User,
    ) -> Table:
        """Создание объекта стол."""
        table = await super().create_object_in_cafe(cafe_id, obj_data, current_user)
        await self.clean_cache(new=True)
        return table

    async def update_object_in_cafe(
        self,
        cafe_id: UUID,
        obj_id: UUID,
        obj_data: TableUpdate,
        current_user: User,
    ) -> Table:
        """Обновление объекта стол."""
        table = await super().update_object_in_cafe(cafe_id, obj_id, obj_data, current_user)
        await self.clean_cache(table_id=obj_id)
        return table


async def get_table_service(session: SessionDep, cafe_service: CafeServiceDep) -> TableService:
    """DI для сервиса столов в кафе."""
    return TableService(session, cafe_service)


TableServiceDep = Annotated[TableService, Depends(get_table_service)]
