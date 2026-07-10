from uuid import UUID

from pydantic import BaseModel, Field

from core.constants import MAX_MEDIA_PATH_LENGTH


class MediaBase(BaseModel):
    """Базовая схема медиафайла (только для чтения)."""

    media_path: str = Field(max_length=MAX_MEDIA_PATH_LENGTH)


class MediaCreate(MediaBase):
    """Схема для создания медиа-записи."""


class MediaInfo(BaseModel):
    """Схема ответа - идентификатор изображения."""

    media_id: UUID
