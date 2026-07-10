from datetime import datetime, time
from typing import Optional, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from schemas.cafe import CafeShortInfo

from core.constants import MAX_DESCRIPTION_LENGTH


class SlotBase(BaseModel):
    """Базовая схема временного слота."""

    start_time: time
    end_time: time
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)


class SlotCreate(SlotBase):
    """Схема для создания нового слота."""

    start_time: time
    end_time: time
    description: Optional[str] = None

    @model_validator(mode='after')
    def check_times(self) -> Self:
        """Проверка start_time < end_time."""
        if self.start_time is not None and self.end_time is not None:
            if self.start_time >= self.end_time:
                raise ValueError('Начало брони не может быть меньше или равно концу брони')
        return self


class SlotUpdate(SlotCreate):
    """Схема для обновления слота (все поля опциональны)."""

    start_time: Optional[time] = None
    end_time: Optional[time] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SlotResponse(SlotBase):
    """Схема ответа с данными слота."""

    id: UUID
    cafe: CafeShortInfo
    start_time: time
    end_time: time
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SlotShortInfo(BaseModel):
    """Краткая информация о временном слоте."""

    id: UUID
    start_time: time
    end_time: time
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
