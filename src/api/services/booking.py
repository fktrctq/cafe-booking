from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.services import CafeServiceDep, SlotServiceDep, TableServiceDep
from api.services.base import BaseService
from api.services.notifications import notify_booking_status
from api.validators.booking import BookingValidator
from cache.cleaner_cache import cache_cleaner_client
from crud import booking_crud
from crud.booking import CRUDBooking
from models import Booking, User, UserRole
from schemas.booking import BookingCreate, BookingUpdate

from core.cache_conf import cache_settings
from core.db import SessionDep


class BookingService(BaseService[Booking, BookingCreate, BookingUpdate]):
    """Сервис для работы с бронированиями."""

    crud: CRUDBooking

    def __init__(
        self,
        session: AsyncSession,
        cafe_service: CafeServiceDep,
        table_service: TableServiceDep,
        slot_service: SlotServiceDep,
    ) -> None:
        """Инициализация сервиса."""
        super().__init__(booking_crud, session)
        self.validator = BookingValidator(session)
        self.cafe_service = cafe_service
        self.table_service = table_service
        self.slot_service = slot_service

    async def clean_cache(self, booking_id: UUID = None, new: bool = False) -> None:
        """Удаление ключей кеша по тегу."""
        tag = None
        if new:
            tag = cache_settings.booking_tag
        if booking_id:
            tag = f'{cache_settings.booking_tag}:{booking_id}'
        if tag is None:
            return
        await cache_cleaner_client.delete_key_by_tag_background(tag)

    async def _check_objects_exist(
        self,
        cafe_id: UUID,
        tables_slots: list,
        current_user: User,
    ) -> None:
        """Проверка существования кафе, столов и слотов для бронирования."""
        await self.cafe_service.get_object_by_role_or_404(cafe_id, current_user)
        for ts in tables_slots:
            await self.table_service.get_object_by_role_or_404(ts.table_id, current_user)
            await self.slot_service.get_object_by_role_or_404(ts.slot_id, current_user)

    async def get_bookings_by_role(
        self,
        current_user: User,
        show_active: Optional[bool] = None,
        cafe_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> list[Booking]:
        """Получение списка бронирований с учетом роли."""
        filter_fields = {}
        if cafe_id:
            filter_fields['cafe_id'] = cafe_id
        if user_id:
            filter_fields['user_id'] = user_id

        if current_user.role == UserRole.USER:
            filter_fields['user_id'] = current_user.id

        if current_user.role == UserRole.MANAGER and cafe_id is not None:
            await self.validator.check_manager_access_to_cafe(cafe_id, current_user)

        return await self.get_all_by_role(current_user, show_active, **filter_fields)

    async def get_booking_by_id(
        self,
        booking_id: UUID,
        current_user: User,
    ) -> Booking:
        """Получение бронирования по ID с проверкой доступа."""
        booking = await self.get_object_or_404(booking_id)
        await self.validator.check_access(booking, current_user)
        return booking

    async def create_booking(
        self,
        booking_data: BookingCreate,
        current_user: User,
    ) -> Booking:
        """Создание нового бронирования."""
        await self.validator.check_booking_date_not_past(booking_data.booking_date)
        await self._check_objects_exist(booking_data.cafe_id, booking_data.tables_slots, current_user)
        await self.validator.check_no_conflicts(booking_data.tables_slots, booking_data.booking_date)
        await self.validator.check_no_user_overlap(
            booking_data.tables_slots,
            booking_data.booking_date,
            current_user.id,
        )
        booking = await self.crud.create(booking_data, self.session, current_user.id)
        notify_booking_status(booking, is_new=True)
        await self.clean_cache(new=True)
        return booking

    async def update_booking(
        self,
        booking_id: UUID,
        booking_data: BookingUpdate,
        current_user: User,
    ) -> Booking:
        """Обновление бронирования."""
        booking = await self.get_booking_by_id(booking_id, current_user)
        await self.validator.check_can_modify(booking)

        tables_slots = booking_data.tables_slots
        if tables_slots is not None:
            booking_date = booking_data.booking_date or booking.booking_date
            await self.validator.check_no_conflicts(
                tables_slots,
                booking_date,
                booking_id,
            )
            await self.validator.check_no_user_overlap(
                tables_slots,
                booking_date,
                booking.user_id,
                booking_id,
            )

        booking = await self.crud.update(booking, booking_data, self.session, tables_slots)
        notify_booking_status(booking)
        await self.clean_cache(booking.id)
        return booking


async def get_booking_service(
    session: SessionDep,
    cafe_service: CafeServiceDep,
    table_service: TableServiceDep,
    slot_service: SlotServiceDep,
) -> BookingService:
    """DI для сервиса бронирований."""
    return BookingService(session, cafe_service, table_service, slot_service)


BookingServiceDep = Annotated[BookingService, Depends(get_booking_service)]
