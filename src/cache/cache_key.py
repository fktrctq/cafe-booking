import logging
from typing import Any, Callable, Optional, Union
from uuid import UUID

logger = logging.getLogger(__name__)


def value_to_str(value: Any) -> Optional[str]:
    """Преобразует значение переменной в строку."""
    try:
        if isinstance(value, (int, str, UUID, bool)):
            return str(value)
        if hasattr(value, 'id'):
            return str(value.id)
        if hasattr(value, 'role'):
            if hasattr(value.role, 'value'):
                return str(value.role.value)
            return str(value.role)
        return None
    except Exception as error:
        logger.error(f'Ошибка преобразования {value} в строку: {error}')
        return None


def extract_fields(kwargs: Any, keys: dict) -> Optional[str]:
    """Извлекает значение из аргументов (поддерживает точечную нотацию).

    Пример:
        keys={
        'role': 'current_user.role',
        'user_id': 'current_user.id',
        'active': 'show_active',
        'cafe': 'cafe_id',
    }
    Возвращает:
        role:ADMIN:user_id:46s4-5df6-...:active:True:cafe:wfvc-we64-...
    """
    if not keys or kwargs is None:
        return None
    parts = []
    try:
        for key_name, path in keys.items():
            current = kwargs
            for part in path.split('.'):
                if isinstance(current, dict):
                    current = current.get(part)
                elif hasattr(current, part):
                    current = getattr(current, part)
                else:
                    current = None

            if current is not None:
                parts.append(f'{key_name}:{current}')

        return ':'.join(parts) if parts else None
    except Exception as error:
        logger.error(f'Ошибка генерации ключа кеша {keys} из аргументов {kwargs}: {error}')
        return None


def get_key_explicit(kwargs: dict, key: Optional[Union[str, dict[str, str], Callable]]) -> Optional[str]:
    """Получение явно указанного имени ключа."""
    if isinstance(key, str):
        if key.strip():
            return key
        return None

    if callable(key):
        try:
            return key(**kwargs)
        except Exception as error:
            logger.error(f'Ошибка генерации ключа через функцию {key.__name__}, аргументы {kwargs}: {error}')
            return None

    if isinstance(key, dict):
        return extract_fields(kwargs, key)
    return None


def auto_gen_key(prefix: str, kwargs: dict, exclude_key: Optional[list[str]] = None) -> Optional[str]:
    """Автоматическая генерация ключа из аргументов kwargs."""
    exclude_key = exclude_key or []
    values_key = [prefix]
    if not kwargs:
        return None
    try:
        for key, value in kwargs.items():
            if key in exclude_key:
                continue
            value_arg = value_to_str(value)
            if value_arg:
                values_key.append(f'{key}:{value_arg}')

        if len(values_key) == 1:
            return None

        return ':'.join(values_key)
    except Exception as error:
        logger.error(f'Ошибка авто-генерации ключа из агруентов {kwargs}: {error}')
        return None


def generate_cache_key(
    prefix: str,
    kwargs: dict,
    exclude_key: Optional[list[str]] = None,
    key: Optional[Union[str, dict[str, str], Callable]] = None,
) -> Optional[str]:
    """Генерируем значение ключа для кеша."""
    if key is not None:
        value_key = get_key_explicit(kwargs, key)
        if value_key:
            return f'{prefix}:{value_key}'
        return None
    return auto_gen_key(prefix, kwargs, exclude_key)


def generate_tags_from_kwars(kwargs: dict, tags: dict[str, str]) -> Optional[set]:
    """Генерация тега из аргументов."""
    try:
        parts = set()
        for tag_name, path in tags.items():
            current = kwargs

            for part in path.split('.'):
                if isinstance(current, dict):
                    current = current.get(part)
                elif hasattr(current, part):
                    current = getattr(current, part)
                else:
                    current = None

            if current is not None:
                parts.add(f'{tag_name}:{current}')

        return parts
    except Exception as error:
        logger.error(f'Ощибка генерации тега {tags} из аргументов {kwargs}: {error}')
        return None


def generate_tags_key(
    kwargs: dict,
    tags: Optional[Union[str, list[str], dict[str, str]]] = None,
) -> Optional[set]:
    """Генерация уникальных тегов для ключа кеша."""
    if not tags or kwargs is None:
        return None
    if isinstance(tags, str):
        return set([tags])
    if isinstance(tags, list):
        return set(tags)
    if isinstance(tags, dict):
        return generate_tags_from_kwars(kwargs, tags)
    return None
