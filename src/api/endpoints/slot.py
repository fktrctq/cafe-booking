from typing import Optional
from uuid import UUID

from fastapi import APIRouter, status

from api.services import SlotServiceDep
from cache.decorator import swr_cache
from middleware.auth import AdminOrManagerDep, CurrentUserDep
from models import Slot
from schemas.slot import SlotCreate, SlotResponse, SlotUpdate

from core.cache_conf import cache_settings

router = APIRouter()
slot_list_cache_swr = swr_cache(
    ttl=cache_settings.slot_ttl,
    stale_ttl=cache_settings.slot_stale_ttl,
    response_model=SlotResponse,
    key_prefix=cache_settings.slot_prefix,
    key={
        'user_role': 'current_user.role',
        'cafe_id': 'cafe_id',
        'cafe_active': 'show_active',
    },
    tags=cache_settings.slot_list_tag,
)


@router.get('/', response_model=list[SlotResponse])
@slot_list_cache_swr
async def get_slots(
    cafe_id: UUID,
    service: SlotServiceDep,
    current_user: CurrentUserDep,
    show_active: Optional[bool] = None,
) -> list[Slot]:
    """Получение списка временных слотов. Разрешено аутентифицированным пользователям."""
    return await service.get_all_objects_by_cafe(cafe_id, current_user, show_active)


slot_by_id_cache_swr = swr_cache(
    ttl=cache_settings.slot_ttl,
    stale_ttl=cache_settings.slot_stale_ttl,
    response_model=SlotResponse,
    key_prefix=cache_settings.slot_prefix,
    key={
        'user_role': 'current_user.role',
        'cafe_id': 'cafe_id',
        'slot_id': 'slot_id',
    },
    tags={
        cache_settings.slot_tag: 'slot_id',
    },
)


@router.get('/{slot_id}', response_model=SlotResponse)
@slot_by_id_cache_swr
async def get_slot(
    cafe_id: UUID,
    slot_id: UUID,
    service: SlotServiceDep,
    current_user: CurrentUserDep,
) -> Slot:
    """Получение временного слота по ID. Разрешено аутентифицированным пользователям."""
    return await service.get_object_by_cafe_or_404(slot_id, cafe_id, current_user)


@router.post('/', response_model=SlotResponse, status_code=status.HTTP_201_CREATED)
async def create_slot(
    cafe_id: UUID,
    slot_data: SlotCreate,
    service: SlotServiceDep,
    current_user: AdminOrManagerDep,
) -> Slot:
    """Создание нового временного слота. Разрешено менеджерам и администраторам."""
    return await service.create_object_in_cafe(cafe_id, slot_data, current_user)


@router.patch('/{slot_id}', response_model=SlotResponse)
async def update_slot(
    cafe_id: UUID,
    slot_id: UUID,
    slot_data: SlotUpdate,
    service: SlotServiceDep,
    current_user: AdminOrManagerDep,
) -> Slot:
    """Обновление данных временного слота. Разрешено менеджерам и администраторам."""
    return await service.update_object_in_cafe(cafe_id, slot_id, slot_data, current_user)
