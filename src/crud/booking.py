from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crud.base import CRUDBase
from models import Booking, BookingStatus, BookingTableSlot
from schemas.booking import BookingCreate, BookingUpdate


class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    """CRUD для модели Booking."""

    async def create(
        self,
        obj_in: BookingCreate,
        session: AsyncSession,
        user_id: UUID,
    ) -> Booking:
        """Создать новое бронирование с парами стол-слот."""
        booking = Booking(
            user_id=user_id,
            cafe_id=obj_in.cafe_id,
            guest_number=obj_in.guest_number,
            booking_date=obj_in.booking_date,
            note=obj_in.note,
        )
        session.add(booking)
        await session.flush()

        for ts in obj_in.tables_slots:
            session.add(
                BookingTableSlot(
                    booking_id=booking.id,
                    table_id=ts.table_id,
                    slot_id=ts.slot_id,
                ),
            )

        await session.commit()
        await session.refresh(booking)
        return booking

    async def update(
        self,
        db_obj: Booking,
        obj_in: BookingUpdate,
        session: AsyncSession,
        tables_slots: Optional[list] = None,
    ) -> Booking:
        """Обновить бронирование."""
        update_data = obj_in.model_dump(exclude_unset=True, exclude={'tables_slots'})

        for key, value in update_data.items():
            setattr(db_obj, key, value)

        if tables_slots is not None:
            for old_ts in db_obj.tables_slots:
                await session.delete(old_ts)
            for ts in tables_slots:
                session.add(
                    BookingTableSlot(
                        booking_id=db_obj.id,
                        table_id=ts.table_id,
                        slot_id=ts.slot_id,
                    ),
                )

        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def get_filtered(
        self,
        session: AsyncSession,
        show_active: Optional[bool] = None,
        cafe_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> list[Booking]:
        """Получить бронирования с фильтрацией."""
        query = select(Booking)
        if cafe_id:
            query = query.where(Booking.cafe_id == cafe_id)
        if user_id:
            query = query.where(Booking.user_id == user_id)
        if show_active is not None:
            query = query.where(Booking.is_active == show_active)

        result = await session.execute(query)
        return result.scalars().all()

    async def get_conflict_for_booking(
        self,
        session: AsyncSession,
        table_id: UUID,
        slot_id: UUID,
        booking_date: date,
        exclude_booking_id: Optional[UUID] = None,
    ) -> Optional[BookingTableSlot]:
        """Получить конфликт для бронирования по конкретным столу, слоту и дате."""
        query = (
            select(BookingTableSlot)
            .join(Booking)
            .where(
                and_(
                    BookingTableSlot.table_id == table_id,
                    BookingTableSlot.slot_id == slot_id,
                    Booking.booking_date == booking_date,
                    Booking.status != BookingStatus.CANCELED,
                ),
            )
        )
        if exclude_booking_id:
            query = query.where(Booking.id != exclude_booking_id)

        result = await session.execute(query)
        return result.scalar()

    async def get_user_bookings_for_date(
        self,
        session: AsyncSession,
        user_id: UUID,
        booking_date: date,
        exclude_booking_id: Optional[UUID] = None,
    ) -> list[BookingTableSlot]:
        """Получить все бронирования пользователя на дату со слотами."""
        query = (
            select(BookingTableSlot)
            .join(Booking)
            .where(
                Booking.user_id == user_id,
                Booking.booking_date == booking_date,
                Booking.status != BookingStatus.CANCELED,
            )
            .options(selectinload(BookingTableSlot.slot))
        )
        if exclude_booking_id:
            query = query.where(Booking.id != exclude_booking_id)

        result = await session.execute(query)
        return result.scalars().all()


booking_crud = CRUDBooking(Booking)
