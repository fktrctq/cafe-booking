from fastapi import APIRouter

from api.endpoints import (
    auth_router,
    booking_router,
    cafe_router,
    health_router,
    media_router,
    schedule_router,
    slot_router,
    table_router,
    user_router,
)

main_router = APIRouter(prefix='/api/v1')

main_router.include_router(
    auth_router,
    prefix='/auth',
    tags=['Аутентификация'],
)

main_router.include_router(
    user_router,
    prefix='/users',
    tags=['Пользователи'],
)
main_router.include_router(
    cafe_router,
    prefix='/cafes',
    tags=['Кафе'],
)
main_router.include_router(
    table_router,
    prefix='/cafes/{cafe_id}/tables',
    tags=['Столы'],
)
main_router.include_router(
    slot_router,
    prefix='/cafes/{cafe_id}/time_slots',
    tags=['Временные слоты'],
)
main_router.include_router(
    booking_router,
    prefix='/booking',
    tags=['Бронирования'],
)
main_router.include_router(
    media_router,
    prefix='/media',
    tags=['Медиа'],
)
main_router.include_router(
    schedule_router,
    prefix='/schedule',
)
main_router.include_router(
    health_router,
    prefix='/health',
    tags=['Health Check'],
)
