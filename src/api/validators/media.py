import io
from pathlib import Path
from typing import Optional

from PIL import Image
from fastapi import HTTPException, status

from core.config import settings
from core.constants import (
    ACCEPTABLE_FORMATS,
    FILE_NOT_FOUND,
    MAX_FILE_SIZE_ERROR,
    READ_IMAGE_ERROR,
)


class MediaValidator:
    """Валидатор для медиа."""

    @staticmethod
    def check_file_exists(file_path: Path) -> Path:
        """Проверка существования файла на диске."""
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=FILE_NOT_FOUND,
            )
        return file_path

    @staticmethod
    def validate_file_extension(filename: Optional[str]) -> None:
        """Проверка расширения файла."""
        ext = filename.rsplit('.', 1)[-1].lower() if filename else ''
        if f'.{ext}' not in settings.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ACCEPTABLE_FORMATS,
            )

    @staticmethod
    def validate_file_size(content: bytes) -> None:
        """Проверка размера файла."""
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=MAX_FILE_SIZE_ERROR,
            )

    @staticmethod
    def validate_image_content(content: bytes) -> None:
        """Проверка, что файл является валидным изображением."""
        try:
            Image.open(io.BytesIO(content))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=READ_IMAGE_ERROR,
            )
