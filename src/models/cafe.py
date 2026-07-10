import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import UUID, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.base_models import Base, CommonMixin
from core.constants import MAX_DESCRIPTION_LENGTH, MAX_NAME_LENGTH, PHONE_LENGTH

if TYPE_CHECKING:
    from models import Booking, Slot, Table, User


class Cafe(CommonMixin, Base):
    """Модель кафе."""

    name: Mapped[str] = mapped_column(String(MAX_NAME_LENGTH), nullable=False)
    address: Mapped[str] = mapped_column(
        String(MAX_NAME_LENGTH),
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(PHONE_LENGTH),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(MAX_DESCRIPTION_LENGTH),
        nullable=True,
    )
    photo_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('media.id', ondelete='SET NULL'),
        nullable=True,
    )
    managers: Mapped[list['User']] = relationship(
        secondary='managers_cafes',
        back_populates='managed_cafes',
        lazy='selectin',
    )
    tables: Mapped[list['Table']] = relationship(
        back_populates='cafe',
        lazy='selectin',
    )
    slots: Mapped[list['Slot']] = relationship(
        back_populates='cafe',
        lazy='selectin',
    )
    bookings: Mapped[list['Booking']] = relationship(
        back_populates='cafe',
        lazy='selectin',
    )

    __table_args__ = (
        UniqueConstraint(
            'name',
            'address',
            'phone',
            name='check_unique_name_address_phone',
        ),
    )

    def __repr__(self) -> str:
        return f'Кафе {self.id} - {self.name}'


class ManagerCafe(Base):
    """Связывающая модель для менеджеров и кафе."""

    __tablename__ = 'managers_cafes'

    manager_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        primary_key=True,
    )
    cafe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('cafes.id', ondelete='CASCADE'),
        primary_key=True,
    )
