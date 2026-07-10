import uuid
from datetime import time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import UUID, CheckConstraint, ForeignKey, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.base_models import Base, CommonMixin
from core.constants import MAX_DESCRIPTION_LENGTH

if TYPE_CHECKING:
    from models import Cafe


class Slot(CommonMixin, Base):
    """Модель для временных слотов."""

    cafe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('cafes.id'),
        nullable=False,
    )
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(
        String(MAX_DESCRIPTION_LENGTH),
        nullable=True,
    )

    cafe: Mapped['Cafe'] = relationship(
        back_populates='slots',
        lazy='selectin',
    )

    __table_args__ = (
        CheckConstraint(
            'start_time < end_time',
            name='check_slot_is_possible',
        ),
    )

    def __repr__(self) -> str:
        return f'Слот id = {self.id}: {self.start_time} - {self.end_time}'
