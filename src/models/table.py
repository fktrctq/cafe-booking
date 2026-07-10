import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.base_models import Base, CommonMixin
from core.constants import MAX_DESCRIPTION_LENGTH

if TYPE_CHECKING:
    from models import Cafe


class Table(CommonMixin, Base):
    """Модель для столиков  кафе."""

    description: Mapped[str | None] = mapped_column(
        String(MAX_DESCRIPTION_LENGTH),
        nullable=True,
    )
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)
    cafe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('cafes.id'),
        nullable=False,
    )
    cafe: Mapped['Cafe'] = relationship(
        back_populates='tables',
        lazy='selectin',
    )

    __table_args__ = (
        CheckConstraint(
            'seat_number > 0',
            name='check_table_seat_number_is_possible',
        ),
    )
