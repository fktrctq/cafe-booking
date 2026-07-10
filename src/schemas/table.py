from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.types import PositiveInt

from schemas.cafe import CafeShortInfo

from core.constants import MAX_DESCRIPTION_LENGTH


class TableBase(BaseModel):
    """Базовая схема стола."""

    seat_number: PositiveInt = Field(description='Количество мест')
    description: Optional[str] = Field(
        None,
        max_length=MAX_DESCRIPTION_LENGTH,
    )


class TableCreate(TableBase):
    """Схема для создания стола."""

    seat_number: PositiveInt = Field(description='Количество мест')
    description: Optional[str] = Field(
        None,
        max_length=MAX_DESCRIPTION_LENGTH,
    )


class TableUpdate(BaseModel):
    """Схема для обновления стола."""

    seat_number: Optional[PositiveInt] = None
    description: Optional[str] = Field(
        None,
        max_length=MAX_DESCRIPTION_LENGTH,
    )
    is_active: Optional[bool] = None


class TableResponse(TableBase):
    """Схема ответа с данными стола."""

    id: UUID
    cafe: CafeShortInfo
    seat_number: int
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TableShortInfo(BaseModel):
    """Краткая информация о столе."""

    id: UUID
    seat_number: int
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
