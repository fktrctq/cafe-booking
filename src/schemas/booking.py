from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from models import BookingStatus
from schemas.cafe import CafeShortInfo
from schemas.slot import SlotShortInfo
from schemas.table import TableShortInfo
from schemas.user import UserShortInfo

from core.constants import MAX_NOTE_LENGTH


class BookingTableSlotInput(BaseModel):
    """Пара стол-слот во входящих данных."""

    table_id: UUID
    slot_id: UUID


class BookingTableSlotShortInfo(BaseModel):
    """Пара стол-слот в ответе."""

    table: TableShortInfo
    slot: SlotShortInfo

    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BaseModel):
    """Схема для создания бронирования."""

    cafe_id: UUID
    tables_slots: list[BookingTableSlotInput] = Field(..., min_length=1)
    guest_number: PositiveInt
    note: Optional[str] = Field(None, max_length=MAX_NOTE_LENGTH)
    booking_date: date


class BookingUpdate(BaseModel):
    """Схема для обновления бронирования."""

    tables_slots: Optional[list[BookingTableSlotInput]] = None
    guest_number: Optional[PositiveInt] = None
    note: Optional[str] = Field(None, max_length=MAX_NOTE_LENGTH)
    status: Optional[BookingStatus] = None
    booking_date: Optional[date] = None
    is_active: Optional[bool] = None


class BookingInfo(BaseModel):
    """Схема ответа с данными бронирования."""

    id: UUID
    user: UserShortInfo
    cafe: CafeShortInfo
    tables_slots: list[BookingTableSlotShortInfo]
    guest_number: int
    note: Optional[str] = None
    status: BookingStatus
    booking_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
