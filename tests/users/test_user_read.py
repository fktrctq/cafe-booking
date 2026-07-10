from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserRole
from tests.constants import (
    CREATED_STATUS,
    INVALID_UUID,
    NOT_FOUND_STATUS,
    OK_STATUS,
    UNKNOWN_UUID,
    USERS_URL,
    USER_DETAIL_URL,
    VALIDATION_ERROR_STATUS,
)
from tests.helpers import (
    assert_password_is_not_returned,
    assert_public_user_schema,
    create_user_in_db,
    get_auth_headers,
)


async def test_get_users_returns_users_list(
    client: AsyncClient,
    db_session: AsyncSession,
    user_payload: dict[str, Any],
    another_user_payload: dict[str, Any],
    admin_payload: dict[str, Any],
) -> None:
    """ADMIN получает список пользователей."""
    first_response = await client.post(USERS_URL, json=user_payload)
    second_response = await client.post(USERS_URL, json=another_user_payload)
    await create_user_in_db(db_session, admin_payload, role=UserRole.ADMIN)

    assert first_response.status_code == CREATED_STATUS
    assert second_response.status_code == CREATED_STATUS

    headers = await get_auth_headers(client, login=admin_payload['email'])

    response = await client.get(USERS_URL, headers=headers)

    assert response.status_code == OK_STATUS

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 3

    for user_data in data:
        assert_public_user_schema(user_data)
        assert_password_is_not_returned(user_data)


async def test_get_user_by_id_success(
    client: AsyncClient,
    db_session: AsyncSession,
    user_payload: dict[str, Any],
    admin_payload: dict[str, Any],
) -> None:
    """ADMIN получает пользователя по id."""
    create_response = await client.post(USERS_URL, json=user_payload)
    created_user = create_response.json()
    await create_user_in_db(db_session, admin_payload, role=UserRole.ADMIN)

    headers = await get_auth_headers(client, login=admin_payload['email'])

    response = await client.get(
        USER_DETAIL_URL.format(user_id=created_user['id']),
        headers=headers,
    )

    assert response.status_code == OK_STATUS

    data = response.json()

    assert_public_user_schema(data)
    assert_password_is_not_returned(data)
    assert data['id'] == created_user['id']
    assert data['username'] == user_payload['username']
    assert data['email'] == user_payload['email']


async def test_get_user_by_unknown_id_returns_404(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_payload: dict[str, Any],
) -> None:
    """Несуществующего пользователя нет в БД, вернёт 404."""
    await create_user_in_db(db_session, admin_payload, role=UserRole.ADMIN)
    headers = await get_auth_headers(client, login=admin_payload['email'])

    response = await client.get(
        USER_DETAIL_URL.format(user_id=UNKNOWN_UUID),
        headers=headers,
    )

    assert response.status_code == NOT_FOUND_STATUS


async def test_get_user_by_invalid_id_returns_422(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_payload: dict[str, Any],
) -> None:
    """Запрос пользователя по невалидному id."""
    await create_user_in_db(db_session, admin_payload, role=UserRole.ADMIN)
    headers = await get_auth_headers(client, login=admin_payload['email'])

    response = await client.get(
        USER_DETAIL_URL.format(user_id=INVALID_UUID),
        headers=headers,
    )

    assert response.status_code == VALIDATION_ERROR_STATUS
