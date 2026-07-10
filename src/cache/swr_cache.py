# Stale-While-Revalidate (SWR)
# Всегда отдавать пользователям старые данные (stale/несвежие), пока в фоне обновляется кеш.
# Данные считаются "достаточно свежими" в течение определенного времени после истечения TTL - stale_ttl.
import asyncio
import logging
import time
from logging import Logger
from typing import Any, Callable, Optional, Type

from fastapi.exceptions import HTTPException
from redis import exceptions as redis_exception

from cache.redis_client import RedisClient, redis_client
from cache.services import deserialize_from_cache, pack_data, serialize_for_cache, unpack_data

from core.cache_conf import cache_settings

logger = logging.getLogger(__name__)


class SWRCache:
    """Кеш с поддержкой Stale-While-Revalidate (SWR)."""

    _LOCK_WAIT_INTERVAL: float = 0.05

    def __init__(self, redis_client: RedisClient, logger: Logger, lock_wait_timeout: float) -> None:
        """инициализация класса."""
        self.redis = redis_client
        self.logger = logger
        self.lock_wait_retries = int(lock_wait_timeout / self._LOCK_WAIT_INTERVAL)

    async def _redis_is_healthy(self) -> bool:
        """Проверка состояния клиента Redis."""
        return await self.redis.is_available()

    async def get_or_update(
        self,
        cache_key: str,
        func: Callable,
        tags: Optional[set[str]] = None,
        ttl: int = 60,
        stale_ttl: int = 60,
        response_model: Optional[Type] = None,
    ) -> Any:
        """Получение данных с SWR стратегией.

        Args:
        cache_key: Явный ключ кеша.
        tags: Теги ключа.
        func: вызываемая функция
        ttl: время, через которое данные становятся stale
        stale_ttl: время, в течение которого можно отдавать stale данные, после истечения ttl
        response_model: Pydantic схема для преобразования ORM объектов.
                        Если не указана, объект сохраняется как есть.

        """
        if not await self._redis_is_healthy():
            return await self._call_func(func)

        # 1. Получаем данные из кеша
        cached = await self.redis.get_key(cache_key)

        if cached is None:
            self.logger.debug(f'Кеш отсутствует: {cache_key} → синхронное обновление!')
            return await self._sync_update(cache_key, tags, func, ttl, stale_ttl, response_model)

        # 2. Получаем возраст данных
        age = await self._get_age_cache(cache_key)
        # 3. Определяем состояние данных
        if age < ttl:
            self.logger.debug(f'Данные из кеша: {cache_key} (age={age:.2f}s)')
            return self._deserialize(cached, response_model)

        if age < ttl + stale_ttl:
            self.logger.debug(
                f'Данные из кеша. Запуск фонового обновления, кеш устарел: {cache_key} (age={age:.2f}s)',
            )
            asyncio.create_task(
                self._background_update(cache_key, tags, func, ttl, stale_ttl, response_model),
            )
            return self._deserialize(cached, response_model)

        self.logger.warning(f'Данные в кеше старые, синхронное обновление: {cache_key} (age={age:.2f}s)')
        return await self._sync_update(cache_key, tags, func, ttl, stale_ttl, response_model)

    async def _sync_update(
        self,
        cache_key: str,
        tags: Optional[set[str]],
        func: Callable,
        ttl: int,
        stale_ttl: int,
        response_model: Optional[Type],
    ) -> Any:
        """Синхронное обновление данных в кеше."""
        lock_key = f'{cache_key}:lock'
        if await self.redis.set_key(key=lock_key, value='lock', nx=True, ex=ttl + stale_ttl):
            try:
                data = await self._call_func(func)
                if data:
                    result = await self._set_cache(cache_key, data, ttl, stale_ttl, response_model)
                    if tags and result:
                        asyncio.create_task(self.set_tags(cache_key, tags, ttl=ttl + stale_ttl))
                return data

            finally:
                await self.redis.delete(lock_key)

        else:
            for _ in range(self.lock_wait_retries):  # Ждем пока другой поток обновит
                await asyncio.sleep(self._LOCK_WAIT_INTERVAL)
                age = await self._get_age_cache(cache_key)
                if age < ttl:
                    cached = await self.redis.get_key(cache_key)
                    if cached is not None:
                        return self._deserialize(cached, response_model)

            return await self._call_func(func)

    async def _background_update(
        self,
        cache_key: str,
        tags: Optional[set[str]],
        func: Callable,
        ttl: int,
        stale_ttl: int,
        response_model: Optional[Type],
    ) -> None:
        """Фоновое обновление устаревших данных в кеше."""
        lock_key = f'{cache_key}:lock'
        if not await self.redis.set_key(key=lock_key, value='lock', nx=True, ex=ttl + stale_ttl):
            return

        try:
            data = await self._call_func(func)
            if data:
                result = await self._set_cache(cache_key, data, ttl, stale_ttl, response_model)
                if tags and result:
                    await self.set_tags(cache_key, tags, ttl=ttl + stale_ttl)
                self.logger.debug(f'Фоновое обновление завершено: {cache_key}')

        except Exception:
            pass  # фоновое обновление не пробрасывает ошибок, завершаем тихо.

        finally:
            await self.redis.delete(lock_key)

    async def _call_func(
        self,
        func: Callable,
    ) -> Optional[Any]:
        """Метод для вызова функции с обработкой ошибок."""
        try:
            return await func()

        except HTTPException as error:
            self.logger.debug(
                f'HTTP исключение "{func.__name__}": {error.status_code} : {error.detail}',
            )
            raise

        except Exception as error:
            self.logger.error(
                f'Ошибка в "{func.__name__}": {error}',
                exc_info=True,
            )
            raise

    async def _invalidate(self, cache_key: str) -> bool:
        """Инвалидация связных ключей кеша."""
        try:
            await self.redis.delete({cache_key, f'{cache_key}:created_at', f'{cache_key}:lock'})
            self.logger.debug(f'Связные ключи кеша удалены: {cache_key}')
            return True
        except Exception as error:
            self.logger.error(f'Ошибка удаления связных ключей кеша {cache_key}: {error}')
            return False

    async def set_tags(self, cache_key: str, tags: set[str], ttl: int) -> bool:
        """Установка тегов для ключа."""
        try:
            keys = {cache_key, f'{cache_key}:created_at', f'{cache_key}:lock'}
            result = await self.redis.set_tags_for_key(keys, tags, ttl)
            logger.debug(f'Установка тегов "{tags}" для ключа "{cache_key}": {result}')
            return result
        except redis_exception.RedisError as error:
            self.logger.error(f'Ошибка записи тегов "{tags}" для ключа "{cache_key}": {error}')
            return False

    async def _set_cache(
        self,
        cache_key: str,
        data: Any,
        ttl: int,
        stale_ttl: int,
        response_model: Optional[Type],
    ) -> bool:
        """Запись данных в кеш, запись ключа время создания кеша."""
        serialized = self._serialize(data, response_model)
        if serialized is not None:
            result = await self.redis.set_key(key=cache_key, value=serialized, ex=ttl + stale_ttl)
            if result:
                return await self.redis.set_key(
                    key=f'{cache_key}:created_at',
                    value=str(time.time()),
                    ex=ttl + stale_ttl,
                )
        return False

    async def _get_age_cache(self, cache_key: str) -> float:
        """Вычисление возраста ключа кеша."""
        created_at = await self.redis.get_key(f'{cache_key}:created_at')
        if created_at is None:
            # Если нет ключа установки времени — считаем, что кеш только создан
            created_at = time.time()
        else:
            try:
                created_at = float(created_at)
            except (ValueError, TypeError):
                return 0
        return time.time() - created_at

    def _serialize(self, data: Any, response_model: Optional[Type]) -> Optional[str]:
        """Сериализация данных для кеша."""
        if response_model:
            return serialize_for_cache(response_model, data)
        return pack_data(data)

    def _deserialize(self, data: str, response_model: Optional[Type]) -> Optional[Any]:
        """Десириализация данных из кеша."""
        if response_model:
            return deserialize_from_cache(response_model, data)
        return unpack_data(data)


swr_cache_redis = SWRCache(redis_client, logger, cache_settings.lock_wait_timeout)
