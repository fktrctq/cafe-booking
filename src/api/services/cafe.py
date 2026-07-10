from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.base import BaseService
from api.validators.cafe import CafeValidator
from cache.cleaner_cache import cache_cleaner_client
from crud import cafe_crud
from models import Cafe, User
from schemas.cafe import CafeCreate, CafeUpdate

from core.cache_conf import cache_settings
from core.db import SessionDep


class CafeService(BaseService[Cafe, CafeCreate, CafeUpdate]):
    """Сервис для работы с кафе."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация сервиса."""
        super().__init__(cafe_crud, session)
        self.validator = CafeValidator(session)

    async def clean_cache(self, cafe_id: UUID = None, new: bool = False) -> None:
        """Удаление ключей кеша по тегу."""
        if new:
            tag = cache_settings.cafe_list_tag
        if cafe_id:
            tag = f'{cache_settings.cafe_tag}:{cafe_id}'
        await cache_cleaner_client.delete_key_by_tag_background(tag)

    async def create_cafe(self, cafe_data: CafeCreate) -> Cafe:
        """Создание нового кафе."""
        await self.validator.check_unique_constraint(
            cafe_data.name,
            cafe_data.address,
            cafe_data.phone,
        )
        await self.clean_cache(new=True)
        return await self.crud.create(cafe_data, self.session)

    async def update_cafe(
        self,
        cafe_id: UUID,
        cafe_data: CafeUpdate,
        current_user: User,
    ) -> Cafe:
        """Обновление кафе."""
        cafe = await self.get_object_or_404(cafe_id)
        await self.validator.check_update_permission(cafe_data, current_user)
        await self.validator.check_unique_constraint(
            cafe_data.name if cafe_data.name is not None else cafe.name,
            cafe_data.address if cafe_data.address is not None else cafe.address,
            cafe_data.phone if cafe_data.phone is not None else cafe.phone,
            cafe_id,
        )
        await self.clean_cache(cafe_id=cafe_id)
        return await self.crud.update(cafe, cafe_data, self.session)


async def get_cafe_service(session: SessionDep) -> CafeService:
    """DI для сервиса кафе."""
    return CafeService(session)


CafeServiceDep = Annotated[CafeService, Depends(get_cafe_service)]
