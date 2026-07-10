import json
import logging
from http import HTTPStatus
from typing import Union

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy_celery_beat.models import ClockedSchedule, CrontabSchedule, IntervalSchedule, PeriodicTask

from celery_core.beat.crud import (
    CRUDSchedule,
    clocked_schedule_crud,
    crontab_schedule_crud,
    interval_schedule_crud,
    periodic_task_crud,
)
from celery_core.beat.schemas import (
    ClockedScheduleCreate,
    ClockedScheduleResponse,
    CrontabScheduleCreate,
    CrontabScheduleResponse,
    IntervalScheduleCreate,
    IntervalScheduleResponse,
    PeriodicTaskCreate,
    PeriodicTaskResponse,
    PeriodicTaskUpdate,
)
from celery_core.beat.validators import check_task_exists_by_name

logger = logging.getLogger(__name__)


def get_schedule(
    schedule_id: int,
    discriminator: str,
    session: Session,
) -> Union[ClockedSchedule, CrontabSchedule, IntervalSchedule]:
    """Получить расписание по ID и типу."""
    if discriminator == 'intervalschedule':
        schedule = interval_schedule_crud.get(schedule_id, session)
    elif discriminator == 'crontabschedule':
        schedule = crontab_schedule_crud.get(schedule_id, session)
    elif discriminator == 'clockedschedule':
        schedule = clocked_schedule_crud.get(schedule_id, session)
    else:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f'Неизвестный тип расписания: {discriminator}',
        )

    if not schedule:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Расписание c ID {schedule_id} типа {discriminator} не найдено',
        )

    return schedule


def build_task_schedule_response(task: PeriodicTask, session: Session) -> PeriodicTaskResponse:
    """Сформировать схему ответа задачи с моделью расписания."""
    task_dict = task.__dict__.copy()
    task_dict['args'] = json.loads(task_dict['args']) if task_dict.get('args') else []
    task_dict['kwargs'] = json.loads(task_dict['kwargs']) if task_dict.get('kwargs') else {}
    response = PeriodicTaskResponse.model_validate(task_dict)
    schedule = get_schedule(task.schedule_id, task.discriminator, session)

    if task.discriminator == 'intervalschedule':
        response.schedule_data = IntervalScheduleResponse.model_validate(schedule)
    elif task.discriminator == 'crontabschedule':
        response.schedule_data = CrontabScheduleResponse.model_validate(schedule)
    elif task.discriminator == 'clockedschedule':
        response.schedule_data = ClockedScheduleResponse.model_validate(schedule)
    return response


def get_task_by_id(task_id: int, session: Session) -> PeriodicTask:
    """получить задачу по ID."""
    task = periodic_task_crud.get(task_id, session)
    if not task:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Задачи с ID {task_id} не существует',
        )
    return task


def remove_schedule(crud: CRUDSchedule, schedule_id: int, session: Session) -> None:
    """Универсальный метод удаления расписания."""
    schedule = crud.get(schedule_id, session)
    if not schedule:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Расписания с ID {schedule_id} не существует',
        )
    crud.remove(schedule, session)


class TaskService:
    """Класс для задач."""

    @staticmethod
    def update_task(task_id: int, data: PeriodicTaskUpdate, session: Session) -> PeriodicTaskResponse:
        """Обновление задачи."""
        task = get_task_by_id(task_id, session)
        if data.schedule_id is not None:
            schedule = get_schedule(data.schedule_id, data.discriminator, session)
            task.schedule_model = schedule
        update_data = data.model_dump(exclude_unset=True, exclude={'schedule_id', 'discriminator'})
        updated_task = periodic_task_crud.update(task, update_data, session)
        return build_task_schedule_response(updated_task, session)

    @staticmethod
    def create_task(data: PeriodicTaskCreate, session: Session) -> PeriodicTaskResponse:
        """Создание задачи."""
        check_task_exists_by_name(data.name, session)
        schedule = get_schedule(data.schedule_id, data.discriminator, session)
        task = periodic_task_crud.create_task_with_schedule(data, schedule, session)
        return build_task_schedule_response(task, session)

    @staticmethod
    def get_all_tasks(session: Session) -> list[PeriodicTaskResponse]:
        """Получение списка всех задач."""
        tasks = periodic_task_crud.get_all(session)
        return [build_task_schedule_response(task, session) for task in tasks]

    @staticmethod
    def get_task(task_id: int, session: Session) -> PeriodicTaskResponse:
        """Получение задачи по ID."""
        task = get_task_by_id(task_id, session)
        return build_task_schedule_response(task, session)

    @staticmethod
    def remove_task(task_id: int, session: Session) -> None:
        """Удалить задачу."""
        task = get_task_by_id(task_id, session)
        periodic_task_crud.remove(task, session)

    @staticmethod
    def enable_task(task_id: int, session: Session) -> PeriodicTaskResponse:
        """Включить задачу."""
        task = get_task_by_id(task_id, session)
        task = periodic_task_crud.update(task, {'enabled': True}, session)
        return build_task_schedule_response(task, session)

    @staticmethod
    def disable_task(task_id: int, session: Session) -> PeriodicTaskResponse:
        """Отключить задачу."""
        task = get_task_by_id(task_id, session)
        task = periodic_task_crud.update(task, {'enabled': False}, session)
        return build_task_schedule_response(task, session)


class ScheduleService:
    """Класс для расписаний."""

    @staticmethod
    def create_clocked_schedule(data: ClockedScheduleCreate, session: Session) -> ClockedSchedule:
        """Создание однократного расписания."""
        clocked_schedule = clocked_schedule_crud.get_by_attributes(
            session,
            **data.model_dump(),
        )
        if clocked_schedule:
            return clocked_schedule
        return clocked_schedule_crud.create(data, session)

    @staticmethod
    def get_all_clocked_schedules(session: Session) -> list[ClockedSchedule]:
        """Список однократных расписаний."""
        return clocked_schedule_crud.get_all(session)

    @staticmethod
    def remove_clocked_schedules(schedules_id: int, session: Session) -> None:
        """Удаление однократного расписания."""
        remove_schedule(clocked_schedule_crud, schedules_id, session)

    @staticmethod
    def create_interval_schedule(data: IntervalScheduleCreate, session: Session) -> IntervalSchedule:
        """Создание интервального расписания."""
        interval_schedule = interval_schedule_crud.get_by_attributes(
            session,
            **data.model_dump(),
        )
        if interval_schedule:
            return interval_schedule
        return interval_schedule_crud.create(data, session)

    @staticmethod
    def get_all_interval_schedules(session: Session) -> list[IntervalSchedule]:
        """Список интервальных расписаний."""
        return interval_schedule_crud.get_all(session)

    @staticmethod
    def remove_interval_schedules(schedules_id: int, session: Session) -> None:
        """Удаление интервального расписания."""
        remove_schedule(interval_schedule_crud, schedules_id, session)

    @staticmethod
    def create_crontab_schedule(data: CrontabScheduleCreate, session: Session) -> CrontabSchedule:
        """Создание хронологического расписания."""
        crontab_schedule = crontab_schedule_crud.get_by_attributes(
            session,
            **data.model_dump(),
        )
        if crontab_schedule:
            return crontab_schedule
        return crontab_schedule_crud.create(data, session)

    @staticmethod
    def get_all_crontab_schedules(session: Session) -> list[CrontabSchedule]:
        """Список хронологических расписаний."""
        return crontab_schedule_crud.get_all(session)

    @staticmethod
    def remove_crontab_schedules(schedules_id: int, session: Session) -> None:
        """Удаление хронологического расписания."""
        remove_schedule(crontab_schedule_crud, schedules_id, session)
