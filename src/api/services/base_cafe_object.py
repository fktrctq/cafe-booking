from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from api.services.base import BaseService, CreateSchemaType, ModelType, UpdateSchemaType
from api.services.cafe import CafeService
from api.validators.cafe_object import CafeObjectValidator
from crud.base import CRUDBase
from models import User


class BaseCafeObjectService(BaseService[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Базовый сервис для объектов, принадлежащих кафе."""

    # crud: Union[CRUDSlot, CRUDTable]

    def __init__(
        self,
        crud: CRUDBase,
        session: AsyncSession,
        cafe_service: CafeService,
    ) -> None:
        """Инициализация сервиса."""
        super().__init__(crud, session)
        self.cafe_service = cafe_service
        self.validator = CafeObjectValidator(session)

    async def get_object_by_cafe_or_404(
        self,
        obj_id: UUID,
        cafe_id: UUID,
        current_user: User,
    ) -> ModelType:
        """Получение объекта с проверкой принадлежности его к кафе."""
        await self.cafe_service.get_object_by_role_or_404(cafe_id, current_user)
        obj = await self.get_object_by_role_or_404(obj_id, current_user)
        return await self.validator.check_object_belongs_to_cafe(obj, cafe_id)

    async def get_all_objects_by_cafe(
        self,
        cafe_id: UUID,
        current_user: User,
        show_active: Optional[bool] = None,
    ) -> list[ModelType]:
        """Получение списка объектов по ID кафе с учетом роли пользователя."""
        await self.cafe_service.get_object_by_role_or_404(cafe_id, current_user)
        return await self.get_all_by_role(current_user, show_active, cafe_id=cafe_id)

    async def create_object_in_cafe(
        self,
        cafe_id: UUID,
        obj_data: CreateSchemaType,
        current_user: User,
    ) -> ModelType:
        """Создать объект в кафе."""
        await self.cafe_service.get_object_by_role_or_404(cafe_id, current_user)
        return await self.crud.create(obj_data, cafe_id, self.session)

    async def update_object_in_cafe(
        self,
        cafe_id: UUID,
        obj_id: UUID,
        obj_data: UpdateSchemaType,
        current_user: User,
    ) -> ModelType:
        """Обновить объект в кафе."""
        obj = await self.get_object_by_cafe_or_404(obj_id, cafe_id, current_user)
        return await self.crud.update(obj, obj_data, self.session)
