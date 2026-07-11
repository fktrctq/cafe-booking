from typing import Optional, TypeVar
from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import PydanticBaseSettingsSource

from core.config import BASE_DIR_PROJECT, settings

User = TypeVar('User')

ENV_DEV = BASE_DIR_PROJECT / 'infra' / '.env.cache'


class CacheSettings(BaseSettings):
    """Пространства имен ключей, тегов, префиксов, ttl и stale_ttl кеша."""

    # общие настройки
    lock_wait_timeout: float = 3  # таймаут ожидания обновления кеша другим потоком, в секундах
    prefix: str = 'dev'
    ttl_cache: int = 90
    stale_ttl_cache: int = 45

    # MiddlewareAuth
    auth_cache: bool = True
    auth_ttl: int = settings.token_life_hours * 1800
    auth_stale_ttl: int = 60
    auth_key: str = 'auth'
    auth_tag: str = 'tag_auth'

    # Booking
    booking_ttl: int = ttl_cache
    booking_stale_ttl: int = stale_ttl_cache
    booking_prefix: str = 'prx_booking'
    booking_tag: str = 'tag_booking'
    booking_list_tag: str = 'tag_bookings'

    # Cafe
    cafe_ttl: int = ttl_cache
    cafe_stale_ttl: int = stale_ttl_cache
    cafe_prefix: str = 'prx_cafe'
    cafe_tag: str = 'tag_cafe'
    cafe_list_tag: str = 'tag_cafes'

    # Slot
    slot_ttl: int = ttl_cache
    slot_stale_ttl: int = stale_ttl_cache
    slot_prefix: str = 'prx_slot'
    slot_tag: str = 'tag_slot'
    slot_list_tag: str = 'tag_slots'

    # Table
    table_ttl: int = ttl_cache
    table_stale_ttl: int = stale_ttl_cache
    table_prefix: str = 'prx_table'
    table_tag: str = 'tag_table'
    table_list_tag: str = 'tag_tables'

    # User
    user_ttl: int = 1800
    user_stale_ttl: int = 300
    user_prefix: str = 'prx_user'
    user_tag: str = 'tag_user'
    user_list_tag: str = 'tag_users'

    model_config = SettingsConfigDict(
        env_file=(ENV_DEV if ENV_DEV.exists() else '.env'),
        env_file_encoding='utf-8',
        extra='ignore',
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Переопределяем приоритеты источников переменных для dev и prom."""
        if ENV_DEV.exists():
            return (init_settings, dotenv_settings, env_settings, file_secret_settings)
        return (init_settings, file_secret_settings, env_settings, dotenv_settings)


cache_settings = CacheSettings()


def bookings_key(
    current_user: User,
    show_active: Optional[bool],
    cafe_id: Optional[UUID],
    user_id: Optional[UUID],
    **kwargs: dict,
) -> str:
    """Генерация ключа кеша для списка бронирований."""
    if current_user.role.value == 'USER':
        return f'user_id:{current_user.id}:user_role:user:cafe_id:{cafe_id}:show_active:True'
    if current_user.role.value == 'MANAGER':
        return f'user_id:{user_id}:user_role:manager:cafe_id:{cafe_id}:show_active:{show_active or True}'
    return f'user_id:{user_id}:user_role:admin:cafe_id:{cafe_id}:show_active:{show_active}'
