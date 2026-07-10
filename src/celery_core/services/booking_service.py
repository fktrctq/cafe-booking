import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models import Booking, BookingStatus, BookingTableSlot, Cafe, Slot

from core.config import settings

logger = logging.getLogger(__name__)


def get_booking_with_relations(booking_id: Any, session: Session) -> Booking:
    """Получить объект бронирования со связями."""
    return (
        session
        .execute(
            select(Booking)
            .options(
                selectinload(Booking.user),
                selectinload(Booking.cafe).selectinload(Cafe.managers),
                selectinload(Booking.tables_slots).selectinload(BookingTableSlot.table),
                selectinload(Booking.tables_slots).selectinload(BookingTableSlot.slot),
            )
            .where(Booking.id == booking_id),
        )
        .scalars()
        .first()
    )


def get_upcoming_bookings(
    reminder_minutes_before: int,
    task_interval_minutes: int,
    session: Session,
) -> list[Any]:
    """Получить список  ID бронирований, требующих напоминания."""
    now = datetime.now(settings.get_time_zone).replace(second=0, microsecond=0)
    target_time = now + timedelta(minutes=reminder_minutes_before)
    delta_size = max(1, task_interval_minutes // 2)
    delta_start = (target_time - timedelta(minutes=delta_size)).time()
    delta_end = (target_time + timedelta(minutes=delta_size)).time()
    logger.debug(
        f'Поиск бронирований для напоминания за {reminder_minutes_before} мин.: '
        f'Текущее время: {now}. Целевое время слота: {target_time.time()}. '
        f'Диапазон поиска: {delta_start} - {delta_end}',
    )
    result = session.execute(
        select(Booking.id)
        .join(Booking.tables_slots)
        .join(BookingTableSlot.slot)
        .where(
            Slot.start_time.between(delta_start, delta_end),
            Booking.booking_date == now.date(),
            Booking.status == BookingStatus.BOOKING,
            Booking.is_active,
            Slot.is_active,
        ),
    )
    return result.scalars().all()
