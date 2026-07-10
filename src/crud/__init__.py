from .booking import CRUDBooking, booking_crud
from .cafe import CRUDCafe, cafe_crud
from .media import CRUDMedia, media_crud
from .slot import CRUDSlot, slot_crud
from .table import CRUDTable, table_crud
from .user import CRUDUser, user_crud

__all__ = [
    'CRUDBooking',
    'CRUDCafe',
    'CRUDMedia',
    'CRUDSlot',
    'CRUDTable',
    'CRUDUser',
    'booking_crud',
    'cafe_crud',
    'media_crud',
    'slot_crud',
    'table_crud',
    'user_crud',
]
