from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud import booking_crud, slot_crud
from models import Booking, BookingStatus, User, UserRole
from schemas.booking import BookingTableSlotInput

from core.constants import (
    ACCESS_DENIED_ERROR,
    BOOKING_ACTIVE_UPDATE_ERROR,
    BOOKING_PAST_CREATE_ERROR,
    BOOKING_PAST_UPDATE_ERROR,
    BOOKING_SLOT_BUSY_ERROR,
    BOOKING_USER_OVERLAP_ERROR,
)


class BookingValidator:
    """Валидатор для бронирований."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация валидатора."""
        self.session = session
        self.crud = booking_crud
        self.slot_crud = slot_crud

    async def check_manager_access_to_cafe(self, cafe_id: UUID, current_user: User) -> None:
        """Проверка, что менеджер имеет доступ к кафе."""
        if current_user.role == UserRole.MANAGER:
            manager_cafe_ids = {c.id for c in current_user.managed_cafes}
            if cafe_id not in manager_cafe_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ACCESS_DENIED_ERROR,
                )

    async def check_access(self, booking: Booking, current_user: User) -> None:
        """Проверка, что пользователь имеет доступ к бронированию."""
        if current_user.role == UserRole.USER and booking.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ACCESS_DENIED_ERROR,
            )
        if current_user.role == UserRole.MANAGER:
            self.check_manager_access_to_cafe(booking.cafe_id, current_user)

    async def check_can_modify(self, booking: Booking) -> None:
        """Проверка, что бронирование можно изменить."""
        if booking.booking_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=BOOKING_PAST_UPDATE_ERROR,
            )
        if booking.status == BookingStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=BOOKING_ACTIVE_UPDATE_ERROR,
            )

    async def check_booking_date_not_past(self, booking_date: date) -> None:
        """Проверка, что дата бронирования не в прошлом."""
        if booking_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=BOOKING_PAST_CREATE_ERROR,
            )

    async def check_no_conflicts(
        self,
        tables_slots: list[BookingTableSlotInput],
        booking_date: date,
        exclude_booking_id: Optional[UUID] = None,
    ) -> None:
        """Проверка, что стол+слот не занят на дату бронирования."""
        for ts in tables_slots:
            conflict = await self.crud.get_conflict_for_booking(
                self.session,
                ts.table_id,
                ts.slot_id,
                booking_date,
                exclude_booking_id,
            )

            if conflict is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=BOOKING_SLOT_BUSY_ERROR,
                )

    async def check_no_user_overlap(
        self,
        tables_slots: list[BookingTableSlotInput],
        booking_date: date,
        user_id: UUID,
        exclude_booking_id: Optional[UUID] = None,
    ) -> None:
        """Проверка, что бронирования пользователя не пересекаются."""
        slot_ids = [ts.slot_id for ts in tables_slots]
        new_slots = await self.slot_crud.get_slots_by_ids(self.session, slot_ids)

        existing_bookings = await self.crud.get_user_bookings_for_date(
            self.session,
            user_id,
            booking_date,
            exclude_booking_id,
        )

        for new_slot in new_slots:
            for existing_booking in existing_bookings:
                existing_slot = existing_booking.slot
                if (
                    new_slot.start_time < existing_slot.end_time
                    and existing_slot.start_time < new_slot.end_time
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=BOOKING_USER_OVERLAP_ERROR,
                    )
