from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from models import UserRole
from schemas.heplers import (
    validate_phone_field,
    validate_tg_id_value,
    validate_username_value,
)

from core.constants import (
    MAX_EMAIL_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_USERNAME_LENGTH,
    PHONE_LENGTH,
)


class UserBase(BaseModel):
    """Базовая схема пользователя."""

    username: str = Field(
        min_length=MIN_USERNAME_LENGTH,
        max_length=MAX_USERNAME_LENGTH,
    )
    email: Optional[EmailStr] = Field(None, max_length=MAX_EMAIL_LENGTH)
    phone: Optional[str] = Field(None, max_length=PHONE_LENGTH)
    tg_id: Optional[str] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, value: str) -> str:
        """Проверяет username."""
        return validate_username_value(value)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        """Нормализует номер телефона."""
        return validate_phone_field(value)

    @field_validator('tg_id')
    @classmethod
    def validate_tg_id(cls, value: Optional[str]) -> Optional[str]:
        """Проверяет Telegram ID."""
        return validate_tg_id_value(value)


class UserCreate(UserBase):
    """Схема для создания пользователя."""

    password: str = Field(min_length=MIN_PASSWORD_LENGTH)


class UserUpdate(BaseModel):
    """Схема для обновления пользователя."""

    username: Optional[str] = Field(
        None,
        min_length=MIN_USERNAME_LENGTH,
        max_length=MAX_USERNAME_LENGTH,
    )
    email: Optional[EmailStr] = Field(None, max_length=MAX_EMAIL_LENGTH)
    phone: Optional[str] = Field(None, max_length=PHONE_LENGTH)
    tg_id: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = Field(None, min_length=MIN_PASSWORD_LENGTH)
    is_active: Optional[bool] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, value: Optional[str]) -> Optional[str]:
        """Проверяет username."""
        return validate_username_value(value)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        """Нормализует номер телефона."""
        return validate_phone_field(value)

    @field_validator('tg_id')
    @classmethod
    def validate_tg_id(cls, value: Optional[str]) -> Optional[str]:
        """Проверяет Telegram ID."""
        return validate_tg_id_value(value)


class UserResponse(UserBase):
    """Схема ответа с данными пользователя."""

    id: UUID
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserShortInfo(UserBase):
    """Краткая информация о пользователе."""

    id: UUID

    model_config = ConfigDict(from_attributes=True)
