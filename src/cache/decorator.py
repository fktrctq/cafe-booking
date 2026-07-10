import asyncio
import functools
import logging
import traceback
from typing import Any, Callable, Optional, Type, TypeVar, Union

from fastapi.exceptions import HTTPException

from cache.cache import cache_redis
from cache.cache_key import generate_cache_key, generate_tags_key
from cache.swr_cache import swr_cache_redis

logger = logging.getLogger(__name__)


T = TypeVar('T')


def cache(
    ttl: int = 60,
    response_model: Optional[Type] = None,
    exclude_key: Optional[list[str]] = None,
    key_prefix: Optional[str] = None,
    key: Optional[Union[str, dict[str, str], Callable]] = None,
    tags: Optional[Union[list[str], dict[str, str]]] = None,
) -> Callable:
    """Декоратор для кеширования результатов.

    Args:
        ttl: Время жизни кеша в секундах
        response_model: Pydantic схема для преобразования ORM объектов.
                        Если не указана, объект сохраняется как есть.
        exclude_key: Список имен аргументов kwargs, исключаемые из генерации ключа кеша.
        key_prefix: префикс ключа для кеша, если не передается используется имя функции.
        key: Явный ключ кеша. Может быть:
                   - str: используется как есть
                   - dict:
                     keys={
                        'role': 'current_user.role',
                        'user_id': 'current_user.id',
                        'active': 'show_active',
                        'cafe': 'cafe_id',
                     }
                   - Callable: функция, возвращающая строку
                     Принимает те же аргументы, что и декорируемая функция
        tags: Теги ключа. Должны содержать уникальные значения ключа, для инвалидации кеша.
                    - list, список тегов
                    - dict: вычисляемые теги из kwargs
                      tags = {
                        'user_id': 'current_user.id',
                        'cafe': 'cafe_id',
                      }

    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(**kwargs: Any) -> T:
            try:
                prefix = key_prefix if key_prefix else func.__name__
                cache_key = generate_cache_key(prefix, kwargs, exclude_key, key)

                if cache_key:
                    cached = await cache_redis.get_cache(cache_key, response_model)
                    if cached is not None:
                        logger.debug(f'Чтение из кеша, ключ: {cache_key}')
                        return cached

                result = await func(**kwargs)

                if cache_key and result is not None:
                    logger.debug(f'Запись в кеш, ключ: {cache_key}')
                    await cache_redis.set_cache(cache_key, ttl, result, response_model)
                    tags_key = generate_tags_key(kwargs, tags)
                    if tags_key:
                        asyncio.create_task(cache_redis.set_tags(cache_key, tags_key))
                return result

            except HTTPException:
                raise
            except Exception as error:
                logger.warning(f'Ошибка в декораторе кеша: {error}')
                logger.warning(f'Тип ошибки: {type(error)}')
                logger.warning(f'Ключевые аргументы: {kwargs}')
                logger.warning(traceback.format_exc())

        return wrapper

    return decorator


def swr_cache(
    ttl: int = 60,
    stale_ttl: int = 120,
    response_model: Optional[Type] = None,
    exclude_key: Optional[list[str]] = None,
    key_prefix: Optional[str] = None,
    key: Optional[Union[str, dict[str, str], Callable]] = None,
    tags: Optional[Union[str, list[str], dict[str, str]]] = None,
) -> Callable:
    """Декоратор с SWR стратегией кеширования.

    Args:
        ttl: Время жизни кеша в секундах
        stale_ttl: Время, в течение которого можно отдавать несвежие данные
        response_model: Pydantic схема для преобразования ORM объектов.
                        Если не указана, объект сохраняется как есть.
        exclude_key: Список имен аргументов kwargs, исключаемые из генерации ключа кеша.
        key_prefix: префикс ключа для кеша, если не передается используется имя функции.
        key: Явный ключ кеша. Может быть:
                   - str: используется как есть
                   - keys={
                        'role': 'current_user.role',
                        'user_id': 'current_user.id',
                        'active': 'show_active',
                        'cafe': 'cafe_id',
                     }
                   - Callable: функция, возвращающая строку
                     Принимает те же аргументы, что и декорируемая функция
        tags: Теги ключа. Должны содержать уникальные значения ключа, для инвалидации кеша.
                    - str, одиночный тег
                    - list, список тегов
                    - dict: вычисляемые теги/тег из kwargs
                      tags = {
                        'user_id': 'current_user.id',
                        'cafe': 'cafe_id',
                      }

    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(**kwargs: Any) -> T:
            prefix = key_prefix if key_prefix else func.__name__
            cache_key = generate_cache_key(prefix, kwargs, exclude_key, key)

            if cache_key:
                tags_key = generate_tags_key(kwargs, tags)

                @functools.wraps(func)
                async def _func() -> Any:
                    """Функция обертка."""
                    return await func(**kwargs)

                return await swr_cache_redis.get_or_update(
                    cache_key=cache_key,
                    func=_func,
                    tags=tags_key,
                    ttl=ttl,
                    stale_ttl=stale_ttl,
                    response_model=response_model,
                )

            return await func(**kwargs)

        return wrapper

    return decorator
