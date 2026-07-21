from typing import Any, Generic, Optional, Type, TypeVar, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Базовый класс для CRUD операций."""

    def __init__(self, model: Type[ModelType]) -> None:
        """Инициализация CRUD."""
        self.model = model

    async def get(self, obj_id: UUID, session: AsyncSession) -> Optional[ModelType]:
        """Получить объект по ID. Возвращает None, если не найден."""
        return await session.get(self.model, obj_id)

    async def get_all(self, session: AsyncSession) -> list[ModelType]:
        """Получить все объекты."""
        db_objs = await session.execute(select(self.model))
        return db_objs.scalars().all()

    async def get_by_attributes(
        self,
        session: AsyncSession,
        many: bool = False,
        **kwargs: Any,
    ) -> Union[Optional[ModelType], list[ModelType]]:
        """получить объект(ы) по атрибутам."""
        query = select(self.model)

        for key, value in kwargs.items():
            attr = getattr(self.model, key)
            query = query.where(attr == value)

        result = await session.execute(query)

        if many:
            return result.scalars().all()

        return result.scalar()

    async def create(self, obj_in: CreateSchemaType, session: AsyncSession) -> ModelType:
        """Создать новый объект."""
        db_obj = self.model(**obj_in.model_dump(exclude_unset=True))
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        session: AsyncSession,
    ) -> ModelType:
        """Обновить объект."""
        for key, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, key, value)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
