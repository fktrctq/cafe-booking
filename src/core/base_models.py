import uuid
from datetime import datetime, timezone

from sqlalchemy import BOOLEAN, UUID, DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


def get_utc_now() -> datetime:
    """Возвращает текущее дата/время UTC."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Базовый класс для всех таблиц.

    В классе определен автоматический нейминг полей.
    """

    metadata = MetaData(
        naming_convention={
            'ix': 'ix_%(column_0_label)s',
            'uq': 'uq_%(table_name)s_%(column_0_name)s',
            'ck': 'ck_%(table_name)s_`%(constraint_name)s`',
            'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
            'pk': 'pk_%(table_name)s',
        },
    )


class CommonMixin:
    """Общий миксин для всех таблиц."""

    @declared_attr
    def __tablename__(cls) -> str:  # noqa: N805
        """Возвращает имя таблицы на основе названия класса."""
        return f'{cls.__name__.lower()}s'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    is_active: Mapped[bool] = mapped_column(BOOLEAN, default=True, server_default='true')
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utc_now,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=get_utc_now,
        server_onupdate=func.now(),
    )
