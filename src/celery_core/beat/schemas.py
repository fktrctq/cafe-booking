import re
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from core.config import settings

CRON_PATTERNS = {
    'minute': r'^(?:\*|(?:[0-9]|[1-5][0-9])|\*/(?:[1-9]|[1-5][0-9]))$',
    'hour': r'^(?:\*|(?:[0-9]|1[0-9]|2[0-3])|\*/(?:[1-9]|1[0-9]|2[0-3]))$',
    'day_of_month': r'^(?:\*|(?:[1-9]|[12][0-9]|3[01])|\*/(?:[1-9]|[12][0-9]|3[01]))$',
    'month_of_year': r'^(?:\*|(?:0?[1-9]|1[0-2])|\*/(?:[1-9]|1[0-2]))$',
    'day_of_week': r'^(?:\*|[0-6]|\*/(?:[1-6]))$',
}

CRON_RANGES = {
    'minute': '0-59',
    'hour': '0-23',
    'day_of_month': '1-31',
    'month_of_year': '1-12',
    'day_of_week': '0-6',
}

TZ = settings.get_time_zone
CLOCKED_TIME_EXAMPLE = datetime.now(TZ).replace(microsecond=0).isoformat()


class IntervalPeriod(str, Enum):
    """Единица измерения."""

    SECONDS = 'seconds'
    MINUTES = 'minutes'
    HOURS = 'hours'
    DAYS = 'days'


class ClockedScheduleCreate(BaseModel):
    """Схема создания однократного расписания."""

    clocked_time: datetime = Field(
        ...,
        description='Дата/Время выполнения задачи.',
        examples=[CLOCKED_TIME_EXAMPLE],
    )
    model_config = ConfigDict(extra='forbid')

    @field_validator('clocked_time')
    @classmethod
    def validator_clocked_fields(cls, v: datetime, info: ValidationInfo) -> datetime:
        """Валидатор времени запуска задачи."""
        now = datetime.now(TZ).replace(microsecond=0, second=0)
        v = v.replace(second=0, microsecond=0)
        if v.tzinfo is None:
            v = v.replace(tzinfo=TZ)
        if v < now:
            raise ValueError(
                f'{info.field_name}: Время запуска задачи не может быть меньше текущего {now}',
            )
        return v


class ClockedScheduleResponse(BaseModel):
    """Response cхема однократного расписания."""

    id: int
    clocked_time: datetime = Field(
        ...,
        description='Дата/Время выполнения задачи.',
        examples=[CLOCKED_TIME_EXAMPLE],
    )
    model_config = ConfigDict(from_attributes=True)


class IntervalScheduleCreate(BaseModel):
    """Схема для создания интервального расписания."""

    every: int = Field(..., ge=1, description='Значение интервала')
    period: IntervalPeriod = Field(..., description='Единица измерения')

    model_config = ConfigDict(extra='forbid')


class IntervalScheduleResponse(IntervalScheduleCreate):
    """Response схема интервального расписания."""

    id: int
    model_config = ConfigDict(from_attributes=True)


class CrontabScheduleBase(BaseModel):
    """Схема хронологического расписания."""

    minute: str = Field(
        default='*',
        description='Минуты (0-59 или * или */N)',
        examples=['30', '59', '*', '*/15'],
    )
    hour: str = Field(
        default='*',
        description='Часы (0-23 или * или */N)',
        examples=['12', '23', '*', '*/2'],
    )
    day_of_week: str = Field(
        default='*',
        description='День недели (0-6 или *), 0=воскресенье',
        examples=['3', '6', '*'],
    )
    day_of_month: str = Field(
        default='*',
        description='День месяца (1-31 или *)',
        examples=['1', '31', '*'],
    )
    month_of_year: str = Field(
        default='*',
        description='Месяц (1-12 или *)',
        examples=['6', '12', '*'],
    )
    timezone: str = Field(
        default=settings.time_zone,
        description='Часовой пояс',
        examples=['Europe/Moscow', 'UTC', 'Asia/Tokyo'],
    )


class CrontabScheduleCreate(CrontabScheduleBase):
    """Схема для создания хронологического расписания."""

    model_config = ConfigDict(extra='forbid')

    @field_validator('minute', 'hour', 'day_of_week', 'day_of_month', 'month_of_year')
    @classmethod
    def validate_crontab_field(cls, v: str, info: ValidationInfo) -> str:
        """Валидация полей cron-выражения (минуты, часы, дни и т.д.)."""
        pattern = CRON_PATTERNS.get(info.field_name)
        if not re.match(pattern, v):
            raise ValueError(
                f'{info.field_name}: допустимые значения — "*" или число в интервале '
                f'{CRON_RANGES.get(info.field_name)}',
            )
        return v


class CrontabScheduleResponse(CrontabScheduleBase):
    """Response схема crontab расписания."""

    id: int
    model_config = ConfigDict(from_attributes=True)


class PeriodicTaskBase(BaseModel):
    """Базовая схема задачи."""

    task: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description='Путь к задаче',
        examples=['tasks.send_upcoming_bookings', 'tasks.send_notification'],
    )
    args: list[Any] = Field(
        default=[],
        description='Список с позиционными аргументами задачи',
        examples=[[60, 10, 'both'], [120, 20, 'client'], [180, 20, 'manager']],
    )
    kwargs: dict[str, Any] = Field(
        default={},
        description='Словарь с именованными аргументами задачи',
        examples=[
            {'reminder_minutes_before': 60, 'task_interval_minutes': 10, 'notify_target': 'both'},
            {'reminder_minutes_before': 120, 'task_interval_minutes': 10, 'notify_target': 'client'},
            {'reminder_minutes_before': 180, 'task_interval_minutes': 10, 'notify_target': 'manager'},
        ],
    )
    enabled: bool = Field(
        default=True,
        description='Активна ли задача',
        examples=[True, False],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description='Название задачи',
        examples=['Отправка уведомлений'],
    )
    description: Optional[str] = Field(
        default=None,
        description='Описание задачи',
        examples=['Ежедневная отправка отчета'],
    )
    queue: Optional[str] = Field(
        default='default',
        description='Очередь брокера для выполнения',
        examples=['default', 'high_priority'],
    )
    priority: Optional[int] = Field(
        None,
        ge=0,
        le=255,
        description='Приоритет задачи (0-255)',
        examples=[0, 255],
    )
    one_off: bool = Field(
        default=False,
        description='Однократная задача',
    )


class PeriodicTaskCreate(PeriodicTaskBase):
    """Схема создания задачи."""

    schedule_id: int = Field(..., description='ID расписания')
    discriminator: str = Field(
        ...,
        description='Тип расписания',
        examples=['intervalschedule', 'crontabschedule', 'clockedschedule'],
    )
    model_config = ConfigDict(extra='forbid')

    @field_validator('queue')
    @classmethod
    def validate_queue(cls, v: Optional[str]) -> Optional[str]:
        """Проверка допустимых символов в названии очереди."""
        if v == '' or v is None:
            return 'default'
        if not re.match(r'^[a-zA-Z0-9_\-.:]+$', v):
            raise ValueError('queue может содержать буквы, цифры, _, -, ., :')
        return v

    @model_validator(mode='after')
    def validate_clocked_one_off(self) -> 'PeriodicTaskCreate':
        """общий валидатор полей схемы создания и обновления."""
        if self.discriminator == 'clockedschedule' and not self.one_off:
            raise ValueError(
                'Для clockedschedule расписания поле one_off должно быть True',
            )
        if self.args and self.kwargs:
            raise ValueError(
                'Нельзя одновременно передавать значения в args и kwargs.',
            )
        return self


class PeriodicTaskResponse(PeriodicTaskBase):
    """Response схема задачи."""

    id: int = Field(description='ID задачи')
    total_run_count: int = Field(default=0, description='Количество запусков')
    start_time: Optional[datetime] = Field(None, description='Время начала выполнения')
    expires: Optional[datetime] = Field(None, description='Дата истечения задачи')
    expire_seconds: Optional[int] = Field(None, description='Секунды до истечения')
    last_run_at: Optional[datetime] = Field(None, description='Время последнего запуска')
    date_changed: datetime = Field(description='Дата последнего изменения')
    discriminator: Optional[str] = Field(
        None,
        description='Тип расписания',
        examples=['intervalschedule', 'crontabschedule', 'clockedschedule'],
    )
    schedule_data: Optional[
        Union[
            IntervalScheduleResponse,
            CrontabScheduleResponse,
            ClockedScheduleResponse,
        ]
    ] = Field(None, description='Объект расписания')

    model_config = ConfigDict(from_attributes=True)


class PeriodicTaskUpdate(PeriodicTaskCreate):
    """Схема обновления задачи."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description='Название задачи')
    task: Optional[str] = Field(None, description='Путь к задаче')
    enabled: Optional[bool] = Field(None, description='Активна ли задача')
    args: Optional[list[Any]] = Field(
        None,
        description='Позиционные аргументы задачи',
        examples=[[60, 10, 'both'], [120, 20, 'client'], [180, 20, 'manager']],
    )
    kwargs: Optional[dict[str, Any]] = Field(
        None,
        description='Именованные аргументы задаи',
        examples=[
            {'reminder_minutes_before': 60, 'task_interval_minutes': 10, 'notify_target': 'both'},
            {'reminder_minutes_before': 120, 'task_interval_minutes': 10, 'notify_target': 'client'},
            {'reminder_minutes_before': 180, 'task_interval_minutes': 10, 'notify_target': 'manager'},
        ],
    )
    schedule_id: Optional[int] = Field(None, description='ID расписания')
    discriminator: Optional[str] = Field(
        None,
        description='Тип расписания (если меняется schedule_id)',
        examples=['intervalschedule', 'crontabschedule', 'clockedschedule'],
    )
    one_off: Optional[bool] = Field(None, description='Однократная задача')

    @model_validator(mode='after')
    def validate_schedule_pair(self) -> 'PeriodicTaskUpdate':
        """Валидатор полей схемы обновления."""
        if self.schedule_id is not None and self.discriminator is None:
            raise ValueError('Поле discriminator обязателен при передаче schedule_id')
        if self.discriminator is not None and self.schedule_id is None:
            raise ValueError('Поле schedule_id обязателен при передаче discriminator')
        return self
