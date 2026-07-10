import logging
from http import HTTPStatus
from typing import Annotated, AsyncIterator

from fastapi import Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings
from core.constants import INTERNAL_DB_ERROR

logger = logging.getLogger(__name__)
engine = create_async_engine(
    settings.database_async_url,
    pool_size=settings.backend_db_pool_size,
    max_overflow=settings.backend_db_max_overflow,
    pool_timeout=settings.backend_db_pool_timeout,
    pool_pre_ping=True,
    pool_recycle=settings.backend_db_pool_recycle,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncIterator[AsyncSession]:
    """Получение асинхронной сессии для FastAPI Depends."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as error:
            await session.rollback()
            logger.error(f'Ошибка при работе с БД : {error}')
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=INTERNAL_DB_ERROR,
            )
        finally:
            await session.close()


SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
