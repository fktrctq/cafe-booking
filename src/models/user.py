from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.base_models import Base, CommonMixin
from core.constants import (
    MAX_EMAIL_LENGTH,
    MAX_HASHED_PASSWORD_LENGTH,
    MAX_USERNAME_LENGTH,
    PHONE_LENGTH,
)

if TYPE_CHECKING:
    from models import Booking, Cafe


class UserRole(str, Enum):
    """Статусы пользователей."""

    ADMIN = 'ADMIN'
    MANAGER = 'MANAGER'
    USER = 'USER'


class User(CommonMixin, Base):
    """Модель пользователя."""

    username: Mapped[str] = mapped_column(
        String(MAX_USERNAME_LENGTH),
        nullable=False,
        unique=True,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(MAX_EMAIL_LENGTH),
        unique=True,
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(PHONE_LENGTH),
        unique=True,
        nullable=True,
    )
    password: Mapped[str] = mapped_column(
        String(MAX_HASHED_PASSWORD_LENGTH),
        nullable=False,
    )
    tg_id: Mapped[Optional[str]] = mapped_column(
        String,
        unique=True,
        nullable=True,
    )

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole),
        default=UserRole.USER,
    )

    managed_cafes: Mapped[list['Cafe']] = relationship(
        secondary='managers_cafes',
        back_populates='managers',
        lazy='selectin',
    )

    bookings: Mapped[list['Booking']] = relationship(
        back_populates='user',
        lazy='selectin',
    )

    __table_args__ = (
        CheckConstraint(
            '(phone IS NOT NULL) OR (email IS NOT NULL)',
            name='check_user_has_contact',
        ),
    )

    def __repr__(self) -> str:
        return f'Пользователь {self.id}: {self.username}, роль = {self.role}'
