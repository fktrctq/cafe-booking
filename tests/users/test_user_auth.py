from typing import Any

import pytest
from httpx import AsyncClient

from tests.constants import (
    AUTH_LOGIN_URL,
    AUTH_TOKEN_FIELD,
    BEARER_TOKEN_PREFIX,
    INVALID_LOGIN,
    INVALID_PASSWORD,
    OK_STATUS,
    TOKEN_TYPE_FIELD,
    VALIDATION_ERROR_STATUS,
    VALID_USER_PASSWORD,
)
from tests.helpers import create_user, make_login_payload


@pytest.mark.parametrize(
    'login_field',
    [
        'email',
        'phone',
    ],
)
async def test_login_user_success_returns_jwt_token(
    client: AsyncClient,
    user_payload: dict[str, Any],
    login_field: str,
) -> None:
    """Авторизация по email или phone возвращает JWT-токен."""
    await create_user(client, user_payload)

    response = await client.post(
        AUTH_LOGIN_URL,
        json=make_login_payload(login=user_payload[login_field]),
    )

    assert response.status_code == OK_STATUS

    data = response.json()

    assert str(data[TOKEN_TYPE_FIELD]).lower() == BEARER_TOKEN_PREFIX.lower()
    assert data[AUTH_TOKEN_FIELD]
    assert isinstance(data[AUTH_TOKEN_FIELD], str)


@pytest.mark.parametrize(
    'login, password',
    [
        (INVALID_LOGIN, VALID_USER_PASSWORD),
        (None, INVALID_PASSWORD),
    ],
)
async def test_login_user_with_invalid_credentials_returns_422(
    client: AsyncClient,
    user_payload: dict[str, Any],
    login: str | None,
    password: str,
) -> None:
    """Неверный логин или пароль не выдает токен."""
    await create_user(client, user_payload)

    response = await client.post(
        AUTH_LOGIN_URL,
        json=make_login_payload(
            login=login or user_payload['email'],
            password=password,
        ),
    )

    assert response.status_code == VALIDATION_ERROR_STATUS


@pytest.mark.parametrize(
    'required_field',
    [
        'login',
        'password',
    ],
)
async def test_login_user_without_required_field_returns_422(
    client: AsyncClient,
    required_field: str,
) -> None:
    """Без login или password авторизация не проходит валидацию."""
    payload = make_login_payload(login=INVALID_LOGIN)
    payload.pop(required_field)

    response = await client.post(AUTH_LOGIN_URL, json=payload)

    assert response.status_code == VALIDATION_ERROR_STATUS
