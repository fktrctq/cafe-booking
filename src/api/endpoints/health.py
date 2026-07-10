import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from kombu import Connection
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cache.redis_client import redis_client

from core.config import settings
from core.db import get_async_session

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
logger = logging.getLogger(__name__)


async def check_redis() -> tuple[bool, str]:
    """Проверка подключения к серверу Redis."""
    try:
        if await redis_client.is_available():
            return True, 'healthy'
        return False, 'unhealthy'
    except Exception as error:
        logger.warning(f'Redis health check failed: {error}')
        return False, str(error)


def check_rabbitmq_sync() -> tuple[bool, str]:
    """Проверка подключения к RabbitMQ."""
    try:
        with Connection(settings.broker_url) as conn:
            conn.connect()
            return True, 'healthy'
    except Exception as error:
        logger.warning(f'RabbitMQ health check failed: {error}')
        return False, str(error)


async def check_database(session: SessionDep) -> tuple[bool, str]:
    """Проверка подключения к БД."""
    try:
        await session.execute(text('SELECT 1'))
        return True, 'healthy'
    except Exception as e:
        logger.critical(f'Database health check failed: {e}')
        return False, str(e)


@router.get('', response_model=dict)
async def health_check(session: SessionDep, response: Response) -> dict:
    """Проверка здоровья сервиса и зависимостей."""
    db_check, db_msg = await check_database(session)
    rmq_check, rmq_msg = await asyncio.to_thread(check_rabbitmq_sync)
    rds_check, rds_msg = await check_redis()
    all_check = all({db_check, rmq_check, rds_check})
    if not all_check:
        response.status_code = 503
    return {
        'status': 'healthy' if all_check else 'unhealthy',
        'checks': {
            'database': db_msg,
            'rabbitmq': rmq_msg,
            'redis': rds_msg,
        },
    }
