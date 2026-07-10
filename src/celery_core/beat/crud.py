import json
from typing import Any, Generic, List, Optional, TypeVar, Union

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
)

from celery_core.beat.schemas import PeriodicTaskCreate, PeriodicTaskUpdate

ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Базовый класс синхронных операций с БД."""

    def __init__(self, model: type[ModelType]) -> None:
        """Инициализация класса."""
        self.model = model

    def get(self, obj_id: int, session: Session) -> Optional[ModelType]:
        """Получить объект по id."""
        return session.get(self.model, obj_id)

    def get_all(self, session: Session) -> List[ModelType]:
        """Получить все объекты."""
        db_objs = session.execute(select(self.model))
        return db_objs.scalars().all()

    def get_by_attributes(self, session: Session, **kwargs: Any) -> Optional[ModelType]:
        """получить объект по одному или нескольким атрибутам."""
        query = select(self.model)
        for key, value in kwargs.items():
            attr = getattr(self.model, key)
            query = query.where(attr == value)
        result = session.execute(query)
        return result.scalars().first()

    def create(self, obj_in: CreateSchemaType, session: Session) -> ModelType:
        """Создать объект."""
        obj_db = self.model(**obj_in.model_dump(exclude_unset=True))
        session.add(obj_db)
        session.commit()
        session.refresh(obj_db)
        return obj_db

    def update(self, db_obj: ModelType, obj_in: UpdateSchemaType, session: Session) -> ModelType:
        """Обновить объект."""
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def remove(self, db_obj: ModelType, session: Session) -> ModelType:
        """Удалить объект."""
        session.delete(db_obj)
        session.commit()
        return db_obj


class CRUDTask(CRUDBase):
    """CRUD класс для задач."""

    def create_task_with_schedule(
        self,
        obj_in: PeriodicTaskCreate,
        schedule: Union[IntervalSchedule, CrontabSchedule, ClockedSchedule],
        session: Session,
    ) -> PeriodicTask:
        """Создать задачу с привязкой к расписанию."""
        obj_in = obj_in.model_dump(exclude={'schedule_id', 'discriminator'})
        obj_in['args'] = json.dumps(obj_in['args'])
        obj_in['kwargs'] = json.dumps(obj_in['kwargs'])
        task = self.model(**obj_in)
        task.schedule_model = schedule
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    def update(
        self,
        db_obj: PeriodicTask,
        obj_in: Union[PeriodicTaskUpdate, dict],
        session: Session,
    ) -> ModelType:
        """Обновить задачу."""
        if not isinstance(obj_in, dict):
            obj_in = obj_in.model_dump(exclude_unset=True)

        if (args := obj_in.get('args')) is not None:
            obj_in['args'] = json.dumps(args)
        if (kwargs := obj_in.get('kwargs')) is not None:
            obj_in['kwargs'] = json.dumps(kwargs)

        for field, value in obj_in.items():
            setattr(db_obj, field, value)

        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj


class CRUDSchedule(CRUDBase):
    """CRUD класс для расписания."""


clocked_schedule_crud = CRUDSchedule(ClockedSchedule)
crontab_schedule_crud = CRUDSchedule(CrontabSchedule)
interval_schedule_crud = CRUDSchedule(IntervalSchedule)
periodic_task_crud = CRUDTask(PeriodicTask)
