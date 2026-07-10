import asyncio
import logging
from typing import Iterable, Optional, Union

from cache.redis_client import RedisClient, redis_client

logger = logging.getLogger(__name__)


class CacheCleaner:
    """Класс инвалидации/удаления ключей кеша.

    Инвалидация данных происходит путем удаления данных из Redis.
    """

    def __init__(self, redis_client: RedisClient, logger: logging.Logger) -> None:
        """инициализация класса."""
        self.redis = redis_client
        self.logger = logger

    async def delete_key_background(self, keys: Union[str, Iterable[str]], prefix: str = None) -> None:
        """Фоновое удаление ключей кеша."""
        asyncio.create_task(self.delete_key(keys, prefix))

    async def delete_key_swr_background(self, keys: Union[str, Iterable[str]], prefix: str = None) -> None:
        """Фоновое удаление связных ключей SWR кеша."""
        asyncio.create_task(self.delete_key_swr(keys, prefix))

    async def delete_key_by_tag_background(self, tags: Union[str, Iterable[str]]) -> None:
        """Фоновое удаление ключей кеша по связному тегу."""
        asyncio.create_task(self.delete_key_by_tag(tags))

    async def delete_key_by_pattern_background(self, patterns: Union[str, Iterable[str]]) -> None:
        """Фоновое удаление ключей кеша по шаблону."""
        asyncio.create_task(self.delete_key_by_pattern(patterns))

    def _add_prefix_for_key(self, keys: Union[str, Iterable[str]], prefix: str = None) -> Optional[set]:
        try:
            if not keys:
                return None
            if isinstance(keys, str):
                if prefix:
                    return {f'{prefix}:{keys}'}
                return {keys}
            if prefix:
                return {f'{prefix}:{key}' for key in keys}
            return set(keys)
        except Exception as error:
            self.logger.error(f'Ошибка формирования ключа кеша для {keys} с префиксом {prefix}: {error}')
            return None

    async def delete_key(
        self,
        cache_key: Union[str, Iterable[str]],
        prefix: str = None,
    ) -> Optional[list]:
        """Удаление ключей кеша."""
        try:
            keys = self._add_prefix_for_key(cache_key, prefix)
            if not keys:
                self.logger.warning(
                    f'Ключи кеша для удаления не переданы! cache_key:{cache_key}, prefix:{prefix}',
                )
                return None
            results = await self.redis.delete(keys)
            self.logger.debug(f'Ключ "{keys}" удален: {results}')
            return results
        except Exception as error:
            self.logger.error(f'Ошибка удаления ключа кеша {cache_key} c префиксом "{prefix}": {error}')
            return None

    async def delete_key_swr(
        self,
        cache_key: Union[str, Iterable[str]],
        prefix: str = None,
    ) -> Optional[list]:
        """Удаление связных ключей swr кеша."""
        try:
            keys = self._add_prefix_for_key(cache_key, prefix)
            if not keys:
                self.logger.warning(
                    f'Ключи кеша для удаления не переданы! cache_key:{cache_key}, prefix:{prefix}',
                )
                return None
            swr_keys = set()
            for key in keys:
                swr_keys.update({key, f'{key}:created_at'})

            results = await self.redis.delete(swr_keys)
            self.logger.debug(f'Связные ключи "{swr_keys}" кеша удалены: {results}')
            return results
        except Exception as error:
            self.logger.error(f'Ошибка удаления связных ключей кеша {keys}: {error}')
            return None

    async def delete_key_by_tag(self, tags: Union[str, Iterable[str]]) -> Optional[list]:
        """Удаление ключей кеша по связному тегу."""
        try:
            if tags is None:
                return None
            if isinstance(tags, str):
                tags = [tags]
            tasks = [self.redis.delete_keys_by_tag(tag) for tag in tags]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            response = []
            for tag, result in zip(tags, results):
                self.logger.debug(f'Результат удаления тега {tag}:{result}')
                response.append({
                    'tag': tag,
                    'result': result,
                    'keys_deleted': len(result) if result and not isinstance(result, Exception) else 0,
                })
            return response
        except Exception as error:
            self.logger.error(f'Ошибка удаления ключей кеша по тегу {tags}: {error}')
            return None

    async def delete_key_by_pattern(self, patterns: Union[str, Iterable[str]]) -> Optional[list]:
        """Удаление ключей кеша по шаблону."""
        try:
            if isinstance(patterns, str):
                patterns = [patterns]
            tasks = [self.redis.delete_keys_by_pattern(pattern) for pattern in patterns]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            response = []
            for pattern, result in zip(patterns, results):
                self.logger.debug(f'Результат удаления по шаблону {pattern}, удалено {result} ключей.')
                response.append({
                    'pattern': pattern,
                    'keys_deleted': result if result else 0,
                })
            return response

        except Exception as error:
            self.logger.error(f'Ошибка удаления ключей кеша по шаблону {patterns}: {error}')
            return None


cache_cleaner_client = CacheCleaner(redis_client, logger)
