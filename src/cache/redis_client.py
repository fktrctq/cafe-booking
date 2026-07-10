import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Iterable, Optional, Union

from redis import asyncio as redis_connect
from redis import exceptions as redis_exceptions
from redis.asyncio import ConnectionPool, Redis

from core.config import settings

logging.getLogger('redis').setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


class RedisClient:
    """Класс клиента Redis."""

    def __init__(
        self,
        host: str = 'redis',
        port: int = 6379,
        db: int = 0,
        max_connections: int = 50,
        max_backoff: int = 60,
    ) -> None:
        """Инициализация класса."""
        self.pool: Optional[ConnectionPool] = None
        self.host = host
        self.port = port
        self.db = db
        self.max_connections = max_connections
        self._is_healthy = False
        self._is_reconnect = False
        self._max_backoff = max_backoff

    async def connect(self) -> bool:
        """Создание пула соединений с Redis."""
        try:
            self.pool = redis_connect.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=False,
                max_connections=self.max_connections,
                socket_keepalive=True,
                socket_timeout=5,
                socket_connect_timeout=2,
                health_check_interval=30,
                retry_on_error=[
                    redis_exceptions.ConnectionError,
                    redis_exceptions.TimeoutError,
                ],
            )
            async with Redis(connection_pool=self.pool) as client:
                result = await client.ping()
            logger.info(
                f'Подключение к серверу Redis установлено "{self.host}:{self.port}": {result}',
            )
            self._is_healthy = result
            return result
        except redis_exceptions.RedisError as error:
            logger.warning(f'Ошибка подключения к серверу Redis "{self.host}:{self.port}": {error}')
            self.pool = None
            self._is_healthy = False
            return False

    async def disconnect(self) -> None:
        """Закрытие пула подключений."""
        if self.pool:
            try:
                await self.pool.aclose()
            except Exception as error:
                logger.warning(f'Ошибка закрытия пула: {error}')
            finally:
                self.pool = None

    async def _reconnect_loop(self) -> None:
        """Фоновый цикл переподключения к Redis с экспоненциальной задержкой."""
        reconnect = 0
        try:
            while True:
                if not self._is_healthy or not self.pool:
                    reconnect += 1
                    wait_time = min(self._max_backoff, 2 ** (reconnect))
                    logger.info(
                        f'Проверка доступности сервера Redis. Повтор:{reconnect}, таймаут: {wait_time} сек.',
                    )
                    await self.disconnect()
                    await asyncio.sleep(wait_time)
                    if await self.connect():
                        break
                else:
                    break
        except Exception as error:
            logger.error(f'Ошибка переподключения к серверу Redis: {error}')
        finally:
            self._is_reconnect = False

    async def is_available(self) -> bool:
        """Проверка состояния соединения с Redis."""
        try:
            if self._is_reconnect:
                return False

            if not self._is_healthy or not self.pool:
                logger.warning(
                    f'Соединение с сервером Redis не установлено. Переподключение "{self.host}:{self.port}"',
                )
                if not self._is_reconnect:
                    self._is_reconnect = True
                    asyncio.create_task(self._reconnect_loop())
                return False

            if not self.pool.can_get_connection():
                logger.warning(
                    f'Отсутствуют свободные соединения в пуле: {self.pool.get_connection_count()}',
                )
                return False

            return True
        except Exception as error:
            logger.error(f'Ощибка проверки состояния соединения с сервером Redis: {error}')
            return False

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[Optional[Redis], None]:
        """Получение клиента Redis."""
        client = None
        try:
            if not await self.is_available():
                yield None
                return

            async with Redis(connection_pool=self.pool) as client:
                yield client

        except (
            redis_exceptions.RedisError,
            redis_exceptions.ConnectionError,
            redis_exceptions.TimeoutError,
        ) as error:
            logger.warning(f'Ошибка при создании клиента Redis: {error}')
            self._is_healthy = False
            raise
        except Exception as error:
            logger.error(f'Неожиданная ошибка при создании клиента Redis: {error}')
            self._is_healthy = False
            raise

    async def get_key(self, key: str) -> Optional[Any]:
        """Получить значение ключа."""
        try:
            async with self.get_client() as client:
                if client is None:
                    return None
                return await client.get(key)
        except (
            redis_exceptions.RedisError,
            redis_exceptions.ConnectionError,
            redis_exceptions.TimeoutError,
        ) as error:
            logger.warning(f'Ошибка чтения кеша, ключ {key}: {error}')
            return None
        except Exception as error:
            logger.error(f'Неожиданная ошибка получения значение ключа: {error}')
            return None

    async def set_key(self, key: str, **kwargs: Any) -> bool:
        """Установить значение ключа с произвольными параметрами.

        Примеры:
            await cache.set_with_options(key, value=value, ex=60)
            await cache.set_with_options(key=key, value=value, ex=ttl)
            await cache.set_with_options(key, value=value, nx=True, ex=60)
            key - имя ключа кеша
            ex - устанавливает истечение срока действия для ключа name на ex=секунд.
            nx - если установлено значение True, устанавливает для ключа name
            value - данные для записи.
                значение на value только если ключ не существует.
        """
        try:
            async with self.get_client() as client:
                if client is None:
                    return False
                return await client.set(name=key, **kwargs)
        except (
            redis_exceptions.RedisError,
            redis_exceptions.ConnectionError,
            redis_exceptions.TimeoutError,
        ) as error:
            logger.warning(f'Ошибка сохранения значения в кеш: {error}')
            return False
        except Exception as error:
            logger.error(f'Не предвиденная ошибка записи в кеш, параметры: {kwargs}, ключ {key}: {error}')
            return False

    async def delete(self, keys: Union[Iterable[str], str]) -> Optional[list]:
        """Удаляет указанные ключи."""
        try:
            async with self.get_client() as client:
                if client is None:
                    return None
                if isinstance(keys, str):
                    keys = [keys]
                async with client.pipeline(transaction=True) as pipe:
                    for key in keys:
                        pipe.unlink(key)
                    return await pipe.execute()
        except (
            redis_exceptions.RedisError,
            redis_exceptions.ConnectionError,
            redis_exceptions.TimeoutError,
        ) as error:
            logger.warning(f'Ошибка удаления ключей: {error}')
            return None
        except Exception as error:
            logger.error(f'Не предвиденная ошибка удаления ключей {keys}: {error}')
            return None

    async def set_tags_for_key(
        self,
        keys: Union[str, Iterable[str]],
        tags: Iterable[str],
        ttl: int,
    ) -> Optional[list]:
        """Добавить теги для ключей."""
        try:
            if not tags or not keys:
                return None
            if isinstance(keys, str):
                keys = [keys]
            async with self.get_client() as client:
                if client is None:
                    return None
                async with client.pipeline(transaction=True) as pipe:
                    for tag in tags:
                        key_tag = f'tag:{tag}'
                        for key in keys:
                            pipe.sadd(key_tag, key)
                        pipe.expire(key_tag, ttl)

                    return await pipe.execute()
        except (
            redis_exceptions.RedisError,
            redis_exceptions.ConnectionError,
            redis_exceptions.TimeoutError,
        ) as error:
            logger.warning(f'Ошибка добавления тегов для ключа {keys}: {error}')
            return None
        except Exception as error:
            logger.error(f'Не предвиденная ошибка добавления тегов для ключа {keys}: {error}')
            return None

    async def get_keys_by_tag(self, tag: str) -> set[str]:
        """Получить все ключи по тегу."""
        try:
            async with self.get_client() as client:
                if client is None:
                    return set()
                keys = await client.smembers(f'tag:{tag}')
                return {key.decode('utf-8') for key in keys}
        except (
            redis_exceptions.RedisError,
            redis_exceptions.ConnectionError,
            redis_exceptions.TimeoutError,
        ) as error:
            logger.warning(f'Ошибка получения ключей по тегу {tag}: {error}')
            return set()
        except Exception as error:
            logger.error(f'Не предвиденная ошибка получения ключей по тегу {tag}: {error}')
            return set()

    async def delete_keys_by_tag(self, tag: str) -> Optional[list]:
        """Удалить все ключи с указанным тегом."""
        try:
            async with self.get_client() as client:
                if client is None:
                    return None
                key_tag = f'tag:{tag}'
                keys = await client.smembers(key_tag)
                async with client.pipeline(transaction=True) as pipe:
                    for key in keys:
                        pipe.unlink(key.decode('utf-8') if isinstance(key, bytes) else key)

                    pipe.unlink(key_tag)
                    return await pipe.execute()
        except (
            redis_exceptions.RedisError,
            redis_exceptions.ConnectionError,
            redis_exceptions.TimeoutError,
        ) as error:
            logger.warning(f'Ошибка удаления ключей по тегу {tag}: {error}')
            return None
        except Exception as error:
            logger.error(f'Не предвиденная ошибка удаления ключей по тегу {tag}: {error}')
            return None

    async def delete_keys_by_pattern(self, pattern: str) -> int:
        """Удаление ключей по шаблону.

        Args:
            pattern: Паттерн для поиска (например, "user:123:*" или "*:bookings:*")

            Примеры шаблонов:
                "user:*"              # все ключи с префиксом "user:"
                "*:cafe"              # все ключи с суффиксом ":cafe"
                "booking:123:*"       # все ключи с префиксом "booking:123:"
                "user:?:cafe"         # один любой символ: user:1:cafe, user:2:cafe
                "user:[123]:*"        # один символ из набора: user:1:*, user:2:*, user:3:*
                "tag:*:user"          # ключи с префиксом "tag:" и суффиксом ":user"
                "tag*"                # все ключи с префиксом "tag"
                "*"                   # ВСЕ ключи (ЖЕСТЬ!)

            Поддерживаемые шаблоны:
                *      - любое количество любых символов (включая ноль)
                ?      - один любой символ
                [ae]   - один символ из набора (a или e)
                [a-z]  - один символ из диапазона
                [^a]   - один символ, не входящий в набор

        """
        try:
            async with self.get_client() as client:
                if client is None:
                    return 0
                deleted = 0
                cursor = 0
                while True:
                    cursor, keys = await client.scan(cursor, match=pattern, count=100)
                    if keys:
                        await client.unlink(*keys)
                        deleted += len(keys)
                    if cursor == 0:
                        break
                return deleted
        except (
            redis_exceptions.RedisError,
            redis_exceptions.ConnectionError,
            redis_exceptions.TimeoutError,
        ) as error:
            logger.warning(f'Ошибка удаления ключей по шаблону {pattern}: {error}')
            return 0
        except Exception as error:
            logger.error(f'Ошибка удаления ключей по шаблону {pattern}: {error}')
            return 0


redis_client = RedisClient(
    host=settings.redis_host,
    port=settings.redis_port,
    db=0,
    max_connections=settings.redis_max_connections,
    max_backoff=settings.redis_max_reconnect_backoff,
)
