from uuid import UUID

from fastapi import APIRouter, UploadFile, status
from fastapi.responses import FileResponse

from api.services import MediaServiceDep
from middleware.auth import AdminOrManagerDep
from schemas.media import MediaInfo

router = APIRouter()


@router.get('/{media_id}')
async def get_media(
    media_id: UUID,
    service: MediaServiceDep,
) -> FileResponse:
    """Получение изображения в формате JPG по ID. Разрешено всем пользователям."""
    file_path = await service.get_media_path(media_id)
    return FileResponse(str(file_path), media_type='image/jpeg')


@router.post(
    '/',
    response_model=MediaInfo,
    status_code=status.HTTP_201_CREATED,
)
async def load_media(
    file: UploadFile,
    service: MediaServiceDep,
    current_user: AdminOrManagerDep,
) -> MediaInfo:
    """Загрузка изображения. Разрешено менеджерам и администраторам."""
    media = await service.save_media(file)
    return MediaInfo(media_id=media.id)
