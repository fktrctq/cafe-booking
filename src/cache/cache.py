from logging import Logger, getLogger
from typing import Any, Optional, Type

from redis import exceptions as redis_exception

from cache.redis_client import RedisClient, redis_client
from cache.services import deserialize_from_cache, pack_data, serialize_for_cache, unpack_data

logger = getLogger(__name__)


class Cache:
    """Обычный кеш, чтение/запись (без стратегий обновления)."""

    def __init__(self, redis_client: RedisClient, logger: Logger) -> None:
        """Инициализация класса."""
        self.redis = redis_client
        self.logger = logger

    async def get_cache(self, cache_key: str, response_model: Optional[Type] = None) -> Optional[Any]:
        """Чтение и десериализация данных из кеша."""
        try:
            cached = await self.redis.get_key(cache_key)
            if cached is None:
                return None

            if response_model:
                return deserialize_from_cache(response_model, cached)
            return unpack_data(cached)

        except redis_exception.RedisError as error:
            self.logger.error(f'Ошибка чтения кеша: {error}')
            return None

    async def set_cache(
        self,
        cache_key: str,
        ttl: int,
        data: Any,
        response_model: Optional[Type] = None,
    ) -> Optional[bool]:
        """Сериализация и запись данных в кеш."""
        try:
            if response_model:
                serializable = serialize_for_cache(response_model, data)
            else:
                serializable = pack_data(data)
            if serializable is None:
                return False
            return await self.redis.set_key(key=cache_key, ex=ttl, value=serializable)
        except redis_exception.RedisError as error:
            self.logger.error(f'Ошибка записи кеша: {error}')
            return None

    async def set_tags(self, cache_key: str, tags: set[str]) -> bool:
        """Установка тегов для ключа."""
        try:
            result = await self.redis.set_tags_for_key(cache_key, tags)
            logger.debug(f'Установка тегов для ключа {cache_key} произведена: {result}')
            return result
        except redis_exception.RedisError as error:
            self.logger.error(f'Ошибка записи тегов для ключа {cache_key}: {error}')
            return False


cache_redis = Cache(redis_client, logger)
