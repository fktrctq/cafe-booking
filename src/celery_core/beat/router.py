from fastapi import APIRouter, Depends
from sqlalchemy_celery_beat.models import ClockedSchedule, CrontabSchedule, IntervalSchedule

from celery_core.beat.dependencies import SessionDep
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
from celery_core.beat.services import ScheduleService, TaskService
from middleware.auth.dependencies import get_current_admin_or_manager

router_schedule = APIRouter(prefix='', tags=['Celery Beat/Управление расписанием'])
router_task = APIRouter(prefix='/task', tags=['Celery Beat/Управление задачами'])


@router_schedule.post('/clocked', response_model=ClockedScheduleResponse)
def create_clocked_schedule(
    data: ClockedScheduleCreate,
    session: SessionDep,
) -> ClockedSchedule:
    """Создание однократного расписания."""
    return ScheduleService.create_clocked_schedule(data, session)


@router_schedule.get('/clocked', response_model=list[ClockedScheduleResponse])
def get_all_clocked_schedules(session: SessionDep) -> list[ClockedSchedule]:
    """Список однократных расписаний."""
    return ScheduleService.get_all_clocked_schedules(session)


@router_schedule.delete('/clocked/{schedules_id}', status_code=204)
def delete_clocked_schedules(schedules_id: int, session: SessionDep) -> None:
    """Удалить однократное расписания."""
    ScheduleService.remove_clocked_schedules(schedules_id, session)


@router_schedule.post('/interval', response_model=IntervalScheduleResponse)
def create_interval_schedule(
    data: IntervalScheduleCreate,
    session: SessionDep,
) -> IntervalSchedule:
    """Создание интервального расписания."""
    return ScheduleService.create_interval_schedule(data, session)


@router_schedule.get('/interval', response_model=list[IntervalScheduleResponse])
def get_all_interval_schedules(session: SessionDep) -> list[IntervalSchedule]:
    """Список интервальных расписаний."""
    return ScheduleService.get_all_interval_schedules(session)


@router_schedule.delete('/interval/{schedules_id}', status_code=204)
def delete_interval_schedules(schedules_id: int, session: SessionDep) -> None:
    """Удалить интервальное расписание."""
    ScheduleService.remove_interval_schedules(schedules_id, session)


@router_schedule.post('/crontab', response_model=CrontabScheduleResponse)
def create_crontab_schedule(
    data: CrontabScheduleCreate,
    session: SessionDep,
) -> CrontabSchedule:
    """Создание хронологического расписания."""
    return ScheduleService.create_crontab_schedule(data, session)


@router_schedule.get('/crontab', response_model=list[CrontabScheduleResponse])
def get_all_crontab_schedules(session: SessionDep) -> list[CrontabSchedule]:
    """Список хронологических расписаний."""
    return ScheduleService.get_all_crontab_schedules(session)


@router_schedule.delete('/crontab/{schedules_id}', status_code=204)
def delete_crontab_schedules(schedules_id: int, session: SessionDep) -> None:
    """Удалить хронологическое расписание."""
    ScheduleService.remove_crontab_schedules(schedules_id, session)


@router_task.post(
    '',
    response_model=PeriodicTaskResponse,
    response_model_exclude_unset=True,  # исключать те поля, которые не были установлены
    response_model_exclude_none=True,  # исключить из ответа те поля, значения которых равны None
)
def create_periodic_task(
    data: PeriodicTaskCreate,
    session: SessionDep,
) -> PeriodicTaskResponse:
    """Создать задачу."""
    return TaskService.create_task(data, session)


@router_task.get('', response_model=list[PeriodicTaskResponse])
def list_periodic_tasks(session: SessionDep) -> list[PeriodicTaskResponse]:
    """Список всех задач."""
    return TaskService.get_all_tasks(session)


@router_task.get('/{task_id}', response_model=PeriodicTaskResponse)
def get_periodic_task(task_id: int, session: SessionDep) -> PeriodicTaskResponse:
    """Получение задачи по ID."""
    return TaskService.get_task(task_id, session)


@router_task.patch(
    '/{task_id}',
    response_model=PeriodicTaskResponse,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
)
def update_periodic_task(
    task_id: int,
    data: PeriodicTaskUpdate,
    session: SessionDep,
) -> PeriodicTaskResponse:
    """Обновление задачи."""
    return TaskService.update_task(task_id, data, session)


@router_task.delete('/{task_id}', status_code=204)
def delete_periodic_task(task_id: int, session: SessionDep) -> None:
    """Удалить задачу."""
    TaskService.remove_task(task_id, session)


@router_task.post('/{task_id}/enable', response_model=PeriodicTaskResponse)
def enable_task(task_id: int, session: SessionDep) -> PeriodicTaskResponse:
    """Включить задачу."""
    return TaskService.enable_task(task_id, session)


@router_task.post('/{task_id}/disable', response_model=PeriodicTaskResponse)
def disable_task(task_id: int, session: SessionDep) -> PeriodicTaskResponse:
    """Отключить задачу."""
    return TaskService.disable_task(task_id, session)


router = APIRouter(dependencies=[Depends(get_current_admin_or_manager)])
router.include_router(router_schedule)
router.include_router(router_task)
