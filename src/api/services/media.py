import io
import uuid
from pathlib import Path
from typing import Annotated
from uuid import UUID

from PIL import Image
from fastapi import Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.base import BaseService
from api.validators.media import MediaValidator
from crud import media_crud
from models import Media
from schemas.media import MediaCreate

from core.config import settings
from core.constants import UPLOAD_CHUNK_SIZE
from core.db import SessionDep


class MediaService(BaseService[Media, MediaCreate, MediaCreate]):
    """Сервис для работы с медиа."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация сервиса."""
        super().__init__(media_crud, session)
        self.validator = MediaValidator()

    async def get_media_path(self, media_id: UUID) -> Path:
        """Получение пути к файлу."""
        media = await self.get_object_or_404(media_id)
        return self.validator.check_file_exists(settings.base_dir_media / media.media_path)

    async def read_upload_file(self, file: UploadFile) -> bytes:
        """Прочтение загруженного файлa с проверкой размера."""
        content = b''
        while True:
            buffer = await file.read(UPLOAD_CHUNK_SIZE)
            if not buffer:
                break
            content += buffer

            self.validator.validate_file_size(content)
        return content

    async def save_media(self, file: UploadFile) -> Media:
        """Сохранение медиа файла и создание записи в БД."""
        self.validator.validate_file_extension(file.filename)
        content = await self.read_upload_file(file)
        self.validator.validate_image_content(content)

        image = self._process_image(content)

        settings.base_dir_media.mkdir(parents=True, exist_ok=True)
        file_name = f'{uuid.uuid4()}.jpg'
        file_path = settings.base_dir_media / file_name
        image.save(file_path, 'JPEG')

        return await self.crud.create(MediaCreate(media_path=file_name), self.session)

    def _process_image(self, content: bytes) -> Image.Image:
        """Обработка изображения."""
        image = Image.open(io.BytesIO(content))

        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            image = image.convert('RGBA')
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        return image


async def get_media_service(session: SessionDep) -> MediaService:
    """DI для сервиса медиа."""
    return MediaService(session)


MediaServiceDep = Annotated[MediaService, Depends(get_media_service)]
