from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.services import CafeServiceDep
from api.services.base_cafe_object import BaseCafeObjectService
from api.validators.cafe_object import SlotValidator
from cache.cleaner_cache import cache_cleaner_client
from crud import slot_crud
from models import Slot, User
from schemas.slot import SlotCreate, SlotUpdate

from core.cache_conf import cache_settings
from core.db import SessionDep


class SlotService(BaseCafeObjectService[Slot, SlotCreate, SlotUpdate]):
    """Сервис для работы с временными слотами в кафе."""

    def __init__(self, session: AsyncSession, cafe_service: CafeServiceDep) -> None:
        """Инициализация сервиса."""
        super().__init__(slot_crud, session, cafe_service)
        self.validator = SlotValidator(session)

    async def clean_cache(self, slot_id: UUID = None, new: bool = False) -> None:
        """Удаление ключей кеша по тегу."""
        if new:
            tag = cache_settings.slot_list_tag
        if slot_id:
            tag = f'{cache_settings.slot_tag}:{slot_id}'
        await cache_cleaner_client.delete_key_by_tag_background(tag)

    async def create_object_in_cafe(
        self,
        cafe_id: UUID,
        obj_data: SlotCreate,
        current_user: User,
    ) -> Slot:
        """Создание временнного слота в кафе с проверкой уникальности."""
        await self.cafe_service.get_object_by_role_or_404(cafe_id, current_user)
        await self.validator.check_unique_slot(
            cafe_id,
            obj_data.start_time,
            obj_data.end_time,
        )
        await self.clean_cache(new=True)
        return await self.crud.create(obj_data, cafe_id, self.session)

    async def update_object_in_cafe(
        self,
        cafe_id: UUID,
        obj_id: UUID,
        obj_data: SlotUpdate,
        current_user: User,
    ) -> Slot:
        """Обновление временного слота в кафе с проверкой уникальности."""
        obj = await self.get_object_by_cafe_or_404(obj_id, cafe_id, current_user)
        await self.validator.check_unique_slot(
            cafe_id,
            obj_data.start_time if obj_data.start_time is not None else obj.start_time,
            obj_data.end_time if obj_data.end_time is not None else obj.end_time,
            obj_id,
        )
        await self.clean_cache(slot_id=obj_id)
        return await self.crud.update(obj, obj_data, self.session)


async def get_slot_service(session: SessionDep, cafe_service: CafeServiceDep) -> SlotService:
    """DI для сервиса временных слотов в кафе."""
    return SlotService(session, cafe_service)


SlotServiceDep = Annotated[SlotService, Depends(get_slot_service)]
