from crud.base import CRUDBase
from models import Media
from schemas.media import MediaCreate


class CRUDMedia(CRUDBase[Media, MediaCreate, MediaCreate]):
    """CRUD для модели Media."""


media_crud = CRUDMedia(Media)
