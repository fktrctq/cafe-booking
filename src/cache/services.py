import json
import logging
from typing import Any, Iterable, Optional, Type, Union

import msgpack
from pydantic import ValidationError

from cache.redis_client import redis_client

logger = logging.getLogger(__name__)


def pack_data(data: Any) -> Optional[bytes]:
    """Сериализация данных в msgpack (для неструктурированных данных)."""
    try:
        return msgpack.packb(
            data,
            default=str,  # Для несериализуемых объектов
            use_bin_type=True,  # Корректная работа с байтами
        )
    except Exception as error:
        logger.error(f'Ошибка сериализации в msgpack: {error}')
        return None


def unpack_data(cached_data: bytes) -> Optional[Any]:
    """Десериализация из msgpack (для неструктурированных данных)."""
    try:
        return msgpack.unpackb(
            cached_data,
            raw=False,  # Строки как str, не bytes
            strict_map_key=False,  # разрешить любые типы для ключей
        )
    except Exception as error:
        logger.error(f'Ошибка десериализации из msgpack: {error}')
        return None


def serialize_for_cache(response_model: Type, data: Any) -> Optional[bytes]:
    """Сериализация данных для хранения в кеше."""
    try:
        if isinstance(data, list):
            validated = [response_model.model_validate(item).model_dump(mode='json') for item in data]
            return msgpack.packb(validated)

        return msgpack.packb(
            response_model.model_validate(data).model_dump(mode='json'),
        )

    except ValidationError as error:
        logger.error(f'Ошибка валидации Pydantic для данных из кеша: {error}')
        return None


def deserialize_from_cache(response_model: Type, cached_data: bytes) -> Optional[Any]:
    """Десериализует JSON строку из кеша в Pydantic схему."""
    try:
        data = msgpack.unpackb(cached_data)

        if isinstance(data, list):
            return [response_model.model_validate(item) for item in data]

        return response_model.model_validate(data)

    except (json.JSONDecodeError, TypeError, ValidationError) as error:
        logger.error(f'Ошибка десериализации данных из кеша: {error}')
        return None


# def serialize_for_cache(response_model: Type, data: Any) -> Optional[bytes]:
#     """Сериализация в JSON → bytes."""
#     try:
#         if isinstance(data, list):
#             validated = [response_model.model_validate(item).model_dump(mode='json') for item in data]
#             return json.dumps(validated).encode('utf-8')

#         return json.dumps(response_model.model_validate(data).model_dump_json()).encode('utf-8')
#     except ValidationError as error:
#         logger.error(f'Ошибка сериализации: {error}')
#         return None


# def deserialize_from_cache(response_model: Type, cached_data: bytes) -> Optional[Any]:
#     """Десериализация из bytes → Pydantic модели."""
#     try:
#         data = json.loads(cached_data.decode('utf-8'))

#         if isinstance(data, list):
#             return [response_model.model_validate(item) for item in data]

#         return response_model.model_validate(data)

#     except Exception as error:
#         logger.error(f'Ошибка десериализации: {error}')
#         return None


async def invalidate_key_cache_swr(keys: Union[Iterable, str]) -> bool:
    """Инвалидация ключей SWR кеша."""
    try:
        if isinstance(keys, str):
            return await redis_client.delete({keys, f'{keys}:created_at', f'{keys}:lock'})
        del_key = set()
        for key in keys:
            del_key.update({key, f'{key}:created_at', f'{key}:lock'})
        return await redis_client.delete(del_key)

    except Exception as error:
        logger.error(f'Ошибка инвалидации клбчей кеша {keys}: {error}')
        return False
