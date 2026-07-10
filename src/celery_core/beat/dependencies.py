import logging
from http import HTTPStatus
from typing import Annotated, Generator

from fastapi import Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy_celery_beat.session import SessionManager

from core.config import settings
from core.constants import INTERNAL_DB_ERROR, INTERNAL_SERVER_ERROR

logger = logging.getLogger(__name__)
session_manager = SessionManager()


def get_beat_session() -> Generator[Session, None, None]:
    """Получаем синхронную сессию sqlalchemy_celery_beat для эндпоинтов управления расписанием и задчами."""
    session = session_manager.session_factory(settings.database_sync_url)
    try:
        yield session
        session.commit()
    except SQLAlchemyError as error:
        session.rollback()
        logger.error(f'{INTERNAL_DB_ERROR}: {error}')
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=INTERNAL_DB_ERROR,
        )
    except Exception as error:
        session.rollback()
        logger.critical(f'{INTERNAL_SERVER_ERROR}: {error}')
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=INTERNAL_DB_ERROR,
        )
    finally:
        session.close()


SessionDep = Annotated[Session, Depends(get_beat_session)]
