from celery_core.beat.router import router as schedule_router

from .auth import router as auth_router
from .booking import router as booking_router
from .cafe import router as cafe_router
from .health import router as health_router
from .media import router as media_router
from .slot import router as slot_router
from .table import router as table_router
from .user import router as user_router

__all__ = [
    'auth_router',
    'booking_router',
    'cafe_router',
    'media_router',
    'slot_router',
    'table_router',
    'user_router',
    'health_router',
    'schedule_router',
]
