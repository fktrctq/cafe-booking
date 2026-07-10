from typing import Optional
from uuid import UUID

from fastapi import APIRouter, status

from api.services.booking import BookingServiceDep
from cache.decorator import swr_cache
from middleware.auth import CurrentUserDep
from models import Booking
from schemas.booking import BookingCreate, BookingInfo, BookingUpdate

from core.cache_conf import bookings_key, cache_settings

router = APIRouter()


bookings_cache_swr = swr_cache(
    ttl=cache_settings.booking_ttl,
    stale_ttl=cache_settings.booking_stale_ttl,
    response_model=BookingInfo,
    key_prefix=cache_settings.booking_prefix,
    key=bookings_key,
    tags=cache_settings.booking_tag,
)


@router.get('/', response_model=list[BookingInfo])
@bookings_cache_swr
async def get_bookings(
    service: BookingServiceDep,
    current_user: CurrentUserDep,
    show_active: Optional[bool] = None,
    cafe_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
) -> list[Booking]:
    """Получение списка бронирований.  Разрешено аутентифицированным пользователям."""
    return await service.get_bookings_by_role(
        current_user,
        show_active,
        cafe_id,
        user_id,
    )


booking_by_id_cache_swr = swr_cache(
    ttl=cache_settings.booking_ttl,
    stale_ttl=cache_settings.booking_stale_ttl,
    response_model=BookingInfo,
    key_prefix=cache_settings.booking_prefix,
    key={
        'booking_id': 'booking_id',
        'current_user': 'current_user.id',
    },
    tags={
        cache_settings.booking_tag: 'booking_id',
    },
)


@router.get('/{booking_id}', response_model=BookingInfo)
@booking_by_id_cache_swr
async def get_booking(
    booking_id: UUID,
    service: BookingServiceDep,
    current_user: CurrentUserDep,
) -> Booking:
    """Получение бронирования по ID.  Разрешено аутентифицированным пользователям."""
    return await service.get_booking_by_id(booking_id, current_user)


@router.post('/', response_model=BookingInfo, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    service: BookingServiceDep,
    current_user: CurrentUserDep,
) -> Booking:
    """Создание нового бронирования. Разрешено аутентифицированным пользователям."""
    return await service.create_booking(booking_data, current_user)


@router.patch('/{booking_id}', response_model=BookingInfo)
async def update_booking(
    booking_id: UUID,
    booking_data: BookingUpdate,
    service: BookingServiceDep,
    current_user: CurrentUserDep,
) -> Booking:
    """Обновление бронирования. Разрешено аутентифицированным пользователям."""
    return await service.update_booking(booking_id, booking_data, current_user)
