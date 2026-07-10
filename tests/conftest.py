from collections.abc import AsyncGenerator
from pathlib import Path

import asyncpg
import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings

settings.postgres_db = settings.db_pytest  # подменяем имя БД
from main import app  # noqa: E402

from core.base_models import Base  # noqa: E402
from core.db import get_async_session  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / 'infra' / '.env')


def get_test_database_url() -> str:
    """Получить URL тестовой БД.

    т.к. выше подменили имя базы то сейчас просто получаем database_async_url

    """
    database_url = settings.database_async_url

    if not database_url.endswith(settings.db_pytest):
        raise RuntimeError(
            f'Что то пошло не так, не получается подключится к тестовой базе {settings.db_pytest} '
            f'текущий url {database_url} для подключения.',
        )

    return database_url


async def create_test_database(db_name: str) -> None:
    """Создать тестовую БД, если не существует."""
    conn = await asyncpg.connect(
        user=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database='postgres',
    )

    try:
        exists = await conn.fetchval(
            'SELECT 1 FROM pg_database WHERE datname = $1',
            db_name,
        )

        if exists:
            print(f'✅ База данных "{db_name}" уже существует')
        else:
            await conn.execute(f'CREATE DATABASE {db_name}')
            print(f'✅ Database "{db_name}" created')
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope='session')
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Создать engine для тестовой БД."""
    await create_test_database(settings.db_pytest)

    engine = create_async_engine(
        get_test_database_url(),
        pool_pre_ping=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_database(test_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """Очищать таблицы перед каждым тестом."""
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

    yield


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Создать отдельную async-сессию для теста."""
    testing_session_local = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with testing_session_local() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_engine: AsyncEngine) -> AsyncGenerator[AsyncClient, None]:
    """Создать тестовый HTTP-клиент с переопределённой DB dependency."""
    testing_session_local = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with testing_session_local() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_async_session] = override_get_async_session

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url='http://testserver',
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()
