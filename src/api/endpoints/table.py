from typing import Optional
from uuid import UUID

from fastapi import APIRouter, status

from api.services import TableServiceDep
from cache.decorator import swr_cache
from middleware.auth import AdminOrManagerDep, CurrentUserDep
from models import Table
from schemas.table import TableCreate, TableResponse, TableUpdate

from core.cache_conf import cache_settings

router = APIRouter()
table_list_cache_swr = swr_cache(
    ttl=cache_settings.table_ttl,
    stale_ttl=cache_settings.table_stale_ttl,
    response_model=TableResponse,
    key_prefix=cache_settings.table_prefix,
    key={
        'user_role': 'current_user.role',
        'cafe_id': 'cafe_id',
        'show_active': 'show_active',
    },
    tags=cache_settings.table_list_tag,
)


@router.get('/', response_model=list[TableResponse])
@table_list_cache_swr
async def get_tables(
    cafe_id: UUID,
    service: TableServiceDep,
    current_user: CurrentUserDep,
    show_active: Optional[bool] = None,
) -> list[Table]:
    """Получение списка столиков. Разрешено аутентифицированным пользователям."""
    return await service.get_all_objects_by_cafe(cafe_id, current_user, show_active)


table_cache_swr = swr_cache(
    ttl=cache_settings.table_ttl,
    stale_ttl=cache_settings.table_stale_ttl,
    response_model=TableResponse,
    key_prefix=cache_settings.table_prefix,
    key={
        'user_role': 'current_user.role',
        'cafe_id': 'cafe_id',
        'table_id': 'table_id',
    },
    tags={
        cache_settings.table_tag: 'table_id',
    },
)


@router.get('/{table_id}', response_model=TableResponse)
@table_cache_swr
async def get_table(
    cafe_id: UUID,
    table_id: UUID,
    service: TableServiceDep,
    current_user: CurrentUserDep,
) -> Table:
    """Получение столика по ID. Разрешено аутентифицированным пользователям."""
    return await service.get_object_by_cafe_or_404(table_id, cafe_id, current_user)


@router.post('/', response_model=TableResponse, status_code=status.HTTP_201_CREATED)
async def create_table(
    cafe_id: UUID,
    table_data: TableCreate,
    service: TableServiceDep,
    current_user: AdminOrManagerDep,
) -> Table:
    """Создание нового столика в кафе. Разрешено менеджерам и администраторам."""
    return await service.create_object_in_cafe(cafe_id, table_data, current_user)


@router.patch('/{table_id}', response_model=TableResponse)
async def update_table(
    cafe_id: UUID,
    table_id: UUID,
    table_data: TableUpdate,
    service: TableServiceDep,
    current_user: AdminOrManagerDep,
) -> Table:
    """Обновление данных столика. Разрешено менеджерам и администраторам."""
    return await service.update_object_in_cafe(cafe_id, table_id, table_data, current_user)
