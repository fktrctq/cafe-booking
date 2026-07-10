from uuid import UUID

from fastapi import APIRouter, status

from api.services import UserServiceDep
from cache.decorator import swr_cache
from middleware.auth import AdminOrManagerDep, CurrentUserDep
from models import User
from schemas.user import UserCreate, UserResponse, UserUpdate

from core.cache_conf import cache_settings

router = APIRouter()
all_user_cache_swr = swr_cache(
    ttl=cache_settings.user_ttl,
    stale_ttl=cache_settings.user_stale_ttl,
    response_model=UserResponse,
    key_prefix=cache_settings.user_prefix,
    key={'user_role': 'current_user.role'},
    tags=cache_settings.user_list_tag,
)


@router.get('/', response_model=list[UserResponse])
@all_user_cache_swr
async def get_users(
    service: UserServiceDep,
    current_user: AdminOrManagerDep,
) -> list[User]:
    """Получение списка пользователей. Разрешено менеджерам и администраторам."""
    return await service.get_all_users()


me_cache_swr = swr_cache(
    ttl=cache_settings.user_ttl,
    stale_ttl=cache_settings.user_stale_ttl,
    response_model=UserResponse,
    key_prefix=cache_settings.user_prefix,
    key={'user_id': 'current_user.id'},
    tags={cache_settings.user_tag: 'current_user.id'},
)


@router.get('/me', response_model=UserResponse)
@me_cache_swr
async def get_current_user_profile(current_user: CurrentUserDep) -> User:
    """Получение профиля текущего пользователя. Разрешено аутентифицированным пользователям."""
    return current_user


user_cache_swr = swr_cache(
    ttl=cache_settings.user_ttl,
    stale_ttl=cache_settings.user_stale_ttl,
    response_model=UserResponse,
    key_prefix=cache_settings.user_prefix,
    key={
        'user_id': 'user_id',
        'user_role': 'current_user.role',
    },
    tags={cache_settings.user_tag: 'user_id'},
)


@router.get('/{user_id}', response_model=UserResponse)
@user_cache_swr
async def get_user(
    user_id: UUID,
    service: UserServiceDep,
    current_user: AdminOrManagerDep,
) -> User:
    """Получение пользователя по ID. Разрешено менеджерам и администраторам."""
    return await service.get_user_or_404(user_id)


@router.post('/', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, service: UserServiceDep) -> User:
    """Регистрация нового пользователя."""
    return await service.create_user(user_data)


@router.patch('/me', response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    service: UserServiceDep,
    current_user: CurrentUserDep,
) -> User:
    """Обновление профиля текущего пользователя. Разрешено аутентифицированным пользователям."""
    return await service.update_current_user(user_data, current_user)


@router.patch('/{user_id}', response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    service: UserServiceDep,
    current_user: AdminOrManagerDep,
) -> User:
    """Обновление данных пользователя по ID. Разрешено менеджерам и администраторам."""
    return await service.update_user_by_id(user_id, user_data, current_user)
