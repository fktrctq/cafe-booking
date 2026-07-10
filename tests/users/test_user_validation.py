from typing import Any

import pytest
from httpx import AsyncClient

from tests.constants import (
    BAD_REQUEST_STATUS,
    USERS_URL,
    VALIDATION_ERROR_STATUS,
)


@pytest.mark.parametrize(
    'field, value',
    [
        ('username', 'ab'),
        ('username', 'bad username'),
        ('username', 'bad$username'),
        ('email', 'not-email'),
        ('phone', '123'),
        ('phone', 'not-phone'),
        ('tg_id', 'not-number'),
        ('password', '1234'),
    ],
)
async def test_create_user_with_invalid_fields_returns_422(
    client: AsyncClient,
    user_payload: dict[str, Any],
    field: str,
    value: str,
) -> None:
    """Попытка создания пользователя с невалидным полем."""
    user_payload[field] = value
    response = await client.post(USERS_URL, json=user_payload)
    assert response.status_code == VALIDATION_ERROR_STATUS


@pytest.mark.parametrize(
    'field',
    [
        'username',
        'password',
    ],
)
async def test_create_user_without_required_fields_returns_422(
    client: AsyncClient,
    user_payload: dict[str, Any],
    field: str,
) -> None:
    """Создание пользователя без заполнения обязательных полей."""
    user_payload.pop(field)

    response = await client.post(USERS_URL, json=user_payload)
    assert response.status_code == VALIDATION_ERROR_STATUS


async def test_create_user_without_email_and_phone_returns_error(
    client: AsyncClient,
    user_payload: dict[str, Any],
) -> None:
    """Нельзя создать пользователя без email и без телефона одновременно."""
    user_payload['email'] = None
    user_payload['phone'] = None

    response = await client.post(USERS_URL, json=user_payload)
    assert response.status_code == BAD_REQUEST_STATUS
