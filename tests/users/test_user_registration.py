from typing import Any

from httpx import AsyncClient

from tests.constants import (
    BAD_REQUEST_STATUS,
    CREATED_STATUS,
    DEFAULT_USER_ROLE,
    DUPLICATE_EMAIL_ERROR,
    DUPLICATE_USERNAME_ERROR,
    NORMALIZED_PHONE,
    USERS_URL,
)
from tests.helpers import (
    assert_password_is_not_returned,
    assert_public_user_schema,
    assert_user_matches_payload,
)


async def test_create_user_success(
    client: AsyncClient,
    user_payload: dict[str, Any],
) -> None:
    """Тестирует успешное создание пользователя."""
    response = await client.post(USERS_URL, json=user_payload)
    assert response.status_code == CREATED_STATUS
    data = response.json()

    assert_public_user_schema(data)
    assert_password_is_not_returned(data)
    assert_user_matches_payload(data, user_payload)

    assert data['id']
    assert data['role'] == DEFAULT_USER_ROLE
    assert data['is_active'] is True
    assert data['phone'] == NORMALIZED_PHONE
    assert data['created_at']
    assert data['updated_at']


async def test_create_user_without_email_but_with_phone_success(
    client: AsyncClient,
    user_payload: dict[str, Any],
) -> None:
    """Успешное создание пользователя без email но с номером телефона."""
    user_payload['email'] = None
    response = await client.post(USERS_URL, json=user_payload)
    assert response.status_code == CREATED_STATUS
    data = response.json()

    assert data['email'] is None
    assert data['phone'] == NORMALIZED_PHONE
    assert_password_is_not_returned(data)


async def test_create_user_without_phone_but_with_email_success(
    client: AsyncClient,
    user_payload: dict[str, Any],
) -> None:
    """Успешное создание пользователя без номера телефона но с email."""
    user_payload['phone'] = None

    response = await client.post(USERS_URL, json=user_payload)

    assert response.status_code == CREATED_STATUS

    data = response.json()

    assert data['email'] == user_payload['email']
    assert data['phone'] is None
    assert_password_is_not_returned(data)


async def test_create_user_with_duplicate_username_returns_400(
    client: AsyncClient,
    user_payload: dict[str, Any],
    another_user_payload: dict[str, dict],
) -> None:
    """Создание пользователя с дубликатом имени вернет 400."""
    first_response = await client.post(USERS_URL, json=user_payload)
    assert first_response.status_code == CREATED_STATUS

    another_user_payload['username'] = user_payload['username']
    response = await client.post(USERS_URL, json=another_user_payload)

    assert response.status_code == BAD_REQUEST_STATUS
    assert response.json()['message'] == DUPLICATE_USERNAME_ERROR


async def test_create_user_with_duplicate_email_returns_400(
    client: AsyncClient,
    user_payload: dict[str, Any],
    another_user_payload: dict[str, dict],
) -> None:
    """Создание пользователя с дубликатом email вернет 400."""
    first_response = await client.post(USERS_URL, json=user_payload)
    assert first_response.status_code == CREATED_STATUS

    another_user_payload['email'] = user_payload['email']
    response = await client.post(USERS_URL, json=another_user_payload)

    assert response.status_code == BAD_REQUEST_STATUS
    assert response.json()['message'] == DUPLICATE_EMAIL_ERROR
