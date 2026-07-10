from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.heplers import validate_phone_field
from schemas.user import UserShortInfo

from core.constants import (
    MAX_ADDRESS_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
    MIN_ANYSTR_LENGTH,
    PHONE_LENGTH,
)


class CafeBase(BaseModel):
    """Базовая схема кафе."""

    name: str = Field(..., min_length=MIN_ANYSTR_LENGTH, max_length=MAX_NAME_LENGTH)
    address: str = Field(..., min_length=MIN_ANYSTR_LENGTH, max_length=MAX_ADDRESS_LENGTH)
    phone: str = Field(..., max_length=PHONE_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    photo_id: Optional[UUID] = None


class CafeCreate(CafeBase):
    """Схема для создания кафе."""

    managers_id: list[UUID]

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        """Нормализует номер телефона."""
        return validate_phone_field(value)

    @field_validator('managers_id')
    @classmethod
    def validate_managers_id(cls, value: list[UUID]) -> list[UUID]:
        """Валидация списка менеджеров."""
        if not value:
            raise ValueError('Должен быть указан хотя бы один менеджер.')
        return value


class CafeUpdate(CafeCreate):
    """Схема для обновления кафе."""

    name: Optional[str] = Field(None, min_length=MIN_ANYSTR_LENGTH, max_length=MAX_NAME_LENGTH)
    address: Optional[str] = Field(
        None,
        min_length=MIN_ANYSTR_LENGTH,
        max_length=MAX_ADDRESS_LENGTH,
    )
    phone: Optional[str] = Field(None, max_length=PHONE_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    photo_id: Optional[UUID] = None
    managers_id: Optional[list[UUID]] = None
    is_active: Optional[bool] = None


class CafeResponse(CafeBase):
    """Схема ответа с данными кафе."""

    id: UUID
    managers: list[UserShortInfo]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CafeShortInfo(CafeBase):
    """Краткая информация о кафе."""

    id: UUID

    model_config = ConfigDict(from_attributes=True)
