import re
from typing import Optional

from core.constants import (
    NAME_PATTERN,
    NORMALIZED_PHONE_LENGTH,
    PHONE_PREFIX_LENGTH,
    RU_PHONE_PREFIXES,
)


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """Нормализовать телефон к формату 10 цифр без +7/8.

    Примеры:
    +79123456789 -> 9123456789
    89123456789  -> 9123456789
    9123456789   -> 9123456789
    """
    if phone is None:
        return None

    cleaned_phone = re.sub(r'\D', '', phone)

    if len(cleaned_phone) == PHONE_PREFIX_LENGTH and cleaned_phone[0] in RU_PHONE_PREFIXES:
        return cleaned_phone[1:]

    if len(cleaned_phone) == NORMALIZED_PHONE_LENGTH:
        return cleaned_phone

    raise ValueError(
        'Неверный номер телефона. Разрешенные форматы: +7XXXXXXXXXX, 8XXXXXXXXXX',
    )


def validate_phone_field(value: Optional[str]) -> Optional[str]:
    """Проверка телефонного номера."""
    if not value:
        return None
    return normalize_phone(value)


def validate_username_value(value: Optional[str]) -> Optional[str]:
    """Проверить username."""
    if value is not None and not re.match(NAME_PATTERN, value):
        raise ValueError(
            'Username может содержать только буквы, цифры, подчеркивания и дефисы',
        )
    return value


def validate_tg_id_value(value: Optional[str]) -> Optional[str]:
    """Проверить Telegram ID."""
    if value is not None:
        try:
            int(value)
        except ValueError as exc:
            raise ValueError('Telegram ID должно быть числом') from exc

    return value
