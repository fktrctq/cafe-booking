from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.base_models import Base, CommonMixin
from core.constants import MAX_MEDIA_PATH_LENGTH


class Media(CommonMixin, Base):
    """Модель для хранения медиафайлов."""

    __tablename__ = 'media'

    media_path: Mapped[str] = mapped_column(
        String(MAX_MEDIA_PATH_LENGTH),
        unique=True,
        nullable=False,
    )
