from typing import Optional
from uuid import UUID

from fastapi import APIRouter, status

from api.services import CafeServiceDep
from cache.decorator import swr_cache
from middleware.auth import AdminOrManagerDep, CurrentUserDep
from models import Cafe
from schemas.cafe import CafeCreate, CafeResponse, CafeUpdate

from core.cache_conf import cache_settings

router = APIRouter()

cafe_list_cache_swr = swr_cache(
    ttl=cache_settings.cafe_ttl,
    stale_ttl=cache_settings.cafe_stale_ttl,
    response_model=CafeResponse,
    key_prefix=cache_settings.cafe_prefix,
    key={
        'user_role': 'current_user.role',
        'cafe_active': 'show_active',
    },
    tags=cache_settings.cafe_list_tag,
)


@router.get('/', response_model=list[CafeResponse])
@cafe_list_cache_swr
async def get_cafes(
    service: CafeServiceDep,
    current_user: CurrentUserDep,
    show_active: Optional[bool] = None,
) -> list[Cafe]:
    """Получение списка кафе. Разрешено аутентифицированным пользователям."""
    return await service.get_all_by_role(current_user, show_active)


cafe_by_id_cache_swr = swr_cache(
    ttl=cache_settings.cafe_ttl,
    stale_ttl=cache_settings.cafe_stale_ttl,
    response_model=CafeResponse,
    key_prefix=cache_settings.cafe_prefix,
    key={
        'user_role': 'current_user.role',
        'cafe_id': 'cafe_id',
    },
    tags={cache_settings.cafe_tag: 'cafe_id'},
)


@router.get('/{cafe_id}', response_model=CafeResponse)
@cafe_by_id_cache_swr
async def get_cafe(
    cafe_id: UUID,
    service: CafeServiceDep,
    current_user: CurrentUserDep,
) -> Cafe:
    """Получение кафе по ID. Разрешено аутентифицированным пользователям."""
    return await service.get_object_by_role_or_404(cafe_id, current_user)


@router.post('/', response_model=CafeResponse, status_code=status.HTTP_201_CREATED)
async def create_cafe(
    cafe_data: CafeCreate,
    service: CafeServiceDep,
    current_user: AdminOrManagerDep,
) -> Cafe:
    """Создание нового кафе. Разрешено менеджерам и администраторам."""
    return await service.create_cafe(cafe_data)


@router.patch('/{cafe_id}', response_model=CafeResponse)
async def update_cafe(
    cafe_id: UUID,
    cafe_data: CafeUpdate,
    service: CafeServiceDep,
    current_user: AdminOrManagerDep,
) -> Cafe:
    """Обновление кафе. Разрешено менеджерам и администраторам."""
    return await service.update_cafe(cafe_id, cafe_data, current_user)
