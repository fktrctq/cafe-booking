from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase, CreateSchemaType, ModelType, UpdateSchemaType
from models import User, UserRole

from core.constants import OBJECT_NOT_FOUND_ERROR

ModelType = TypeVar('ModelType', bound=ModelType)
CreateSchemaType = TypeVar('CreateSchemaType', bound=CreateSchemaType)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=UpdateSchemaType)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Базовый сервис с CRUD операциями."""

    def __init__(self, crud: CRUDBase, session: AsyncSession) -> None:
        """Инициализация сервиса."""
        self.crud = crud
        self.session = session

    async def get_object_or_404(
        self,
        obj_id: UUID,
        show_active: Optional[bool] = None,
    ) -> ModelType:
        """Получение объекта по ID. Выбрасывает ошибку 404, если не найден."""
        obj = await self.crud.get(obj_id, self.session)

        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=OBJECT_NOT_FOUND_ERROR,
            )
        if show_active is not None:
            if obj.is_active != show_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=OBJECT_NOT_FOUND_ERROR,
                )
        return obj

    async def get_object_by_role_or_404(
        self,
        obj_id: UUID,
        current_user: User,
    ) -> ModelType:
        """Получение объекта по ID с проверкой прав и проверкой существования."""
        if current_user.role == UserRole.USER:
            return await self.get_object_or_404(obj_id, show_active=True)
        return await self.get_object_or_404(obj_id)

    async def get_all_by_role(
        self,
        current_user: User,
        show_active: Optional[bool] = None,
        filter_attr: Optional[tuple[str, Any]] = None,
    ) -> list[ModelType]:
        """Получение списка объектов с учетом роли пользователя.

        Можно отфильтровать объекты по дополнительному атрибуту.
        """
        if filter_attr:
            objects = await self.crud.get_by_attr(
                filter_attr[0],
                filter_attr[1],
                self.session,
                many=True,
            )
        else:
            objects = await self.crud.get_all(self.session)

        if current_user.role == UserRole.USER:
            return [obj for obj in objects if obj.is_active is True]

        if current_user.role == UserRole.MANAGER:
            if show_active is not None:
                return [obj for obj in objects if obj.is_active == show_active]
            return [obj for obj in objects if obj.is_active is True]

        if show_active is not None:
            return [obj for obj in objects if obj.is_active == show_active]
        return objects
