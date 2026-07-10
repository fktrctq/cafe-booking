import uuid
from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    UUID,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.base_models import Base, CommonMixin
from core.constants import MAX_NOTE_LENGTH

if TYPE_CHECKING:
    from models import Cafe, Slot, Table, User


class BookingStatus(str, Enum):
    """Статусы бронирования."""

    BOOKING = 'BOOKING'
    ACTIVE = 'ACTIVE'
    COMPLETED = 'COMPLETED'
    CANCELED = 'CANCELED'


class BookingTableSlot(Base):
    """Промежуточная таблица: бронирование — стол — слот."""

    __tablename__ = 'booking_table_slots'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('bookings.id', ondelete='CASCADE'),
        nullable=False,
    )
    table_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('tables.id'),
        nullable=False,
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('slots.id'),
        nullable=False,
    )

    booking: Mapped['Booking'] = relationship(back_populates='tables_slots')
    table: Mapped['Table'] = relationship(lazy='selectin')
    slot: Mapped['Slot'] = relationship(lazy='selectin')


class Booking(CommonMixin, Base):
    """Модель бронирования."""

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=False,
    )
    cafe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('cafes.id'),
        nullable=False,
    )
    guest_number: Mapped[int] = mapped_column(Integer, nullable=False)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus),
        default=BookingStatus.BOOKING,
    )
    note: Mapped[Optional[str]] = mapped_column(
        String(MAX_NOTE_LENGTH),
        nullable=True,
    )

    user: Mapped['User'] = relationship(
        back_populates='bookings',
        lazy='selectin',
    )
    cafe: Mapped['Cafe'] = relationship(
        back_populates='bookings',
        lazy='selectin',
    )
    tables_slots: Mapped[list['BookingTableSlot']] = relationship(
        back_populates='booking',
        lazy='selectin',
        cascade='all, delete-orphan',
    )

    __table_args__ = (
        CheckConstraint(
            'booking_date >= CURRENT_DATE',
            name='check_booking_date_is_not_past',
        ),
    )
