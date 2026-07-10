from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserRole
from tests.constants import (
    BAD_REQUEST_STATUS,
    CREATED_STATUS,
    USERS_URL,
    USER_DETAIL_URL,
)
from tests.helpers import (
    create_user_in_db,
    get_auth_headers,
    make_unique_user_payload,
)


@pytest.mark.parametrize(
    'unique_field',
    [
        'phone',
        'tg_id',
    ],
)
async def test_create_user_with_duplicate_phone_or_tg_id_returns_400(
    client: AsyncClient,
    unique_field: str,
) -> None:
    """Test user creation with duplicate phone or tg_id returns 400."""
    first_payload = make_unique_user_payload(index=1)
    second_payload = make_unique_user_payload(index=2)

    second_payload[unique_field] = first_payload[unique_field]

    first_response = await client.post(USERS_URL, json=first_payload)
    assert first_response.status_code == CREATED_STATUS

    response = await client.post(USERS_URL, json=second_payload)

    assert response.status_code == BAD_REQUEST_STATUS


@pytest.mark.parametrize(
    'unique_field',
    [
        'username',
        'email',
        'phone',
        'tg_id',
    ],
)
async def test_update_user_with_duplicate_unique_field_returns_400(
    client: AsyncClient,
    db_session: AsyncSession,
    unique_field: str,
    admin_payload: dict[str, Any],
) -> None:
    """Test user update with duplicate unique field returns 400."""
    first_payload: dict[str, Any] = make_unique_user_payload(index=1)
    second_payload: dict[str, Any] = make_unique_user_payload(index=2)

    first_response = await client.post(USERS_URL, json=first_payload)
    second_response = await client.post(USERS_URL, json=second_payload)
    await create_user_in_db(db_session, admin_payload, role=UserRole.ADMIN)

    assert first_response.status_code == CREATED_STATUS
    assert second_response.status_code == CREATED_STATUS

    first_user = first_response.json()
    second_user = second_response.json()

    headers = await get_auth_headers(client, login=admin_payload['email'])

    response = await client.patch(
        USER_DETAIL_URL.format(user_id=second_user['id']),
        json={unique_field: first_user[unique_field]},
        headers=headers,
    )

    assert response.status_code == BAD_REQUEST_STATUS
