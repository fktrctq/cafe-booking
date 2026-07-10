from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserRole
from tests.constants import (
    INVALID_UUID,
    NOT_FOUND_STATUS,
    OK_STATUS,
    UNKNOWN_UUID,
    UPDATED_EMAIL,
    UPDATED_NORMALIZED_PHONE,
    UPDATED_PHONE,
    UPDATED_TG_ID,
    UPDATED_USERNAME,
    UPDATED_USER_PASSWORD,
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


async def test_update_user_success(
    client: AsyncClient,
    db_session: AsyncSession,
    user_payload: dict[str, Any],
    admin_payload: dict[str, Any],
) -> None:
    """ADMIN успешно обновляет существующего пользователя."""
    create_response = await client.post(USERS_URL, json=user_payload)
    created_user = create_response.json()
    await create_user_in_db(db_session, admin_payload, role=UserRole.ADMIN)

    headers = await get_auth_headers(client, login=admin_payload['email'])

    update_payload = {
        'username': UPDATED_USERNAME,
        'email': UPDATED_EMAIL,
        'phone': UPDATED_PHONE,
        'tg_id': UPDATED_TG_ID,
    }

    response = await client.patch(
        USER_DETAIL_URL.format(user_id=created_user['id']),
        json=update_payload,
        headers=headers,
    )

    assert response.status_code == OK_STATUS

    data = response.json()

    assert_public_user_schema(data)
    assert_password_is_not_returned(data)

    assert data['id'] == created_user['id']
    assert data['username'] == UPDATED_USERNAME
    assert data['email'] == UPDATED_EMAIL
    assert data['phone'] == UPDATED_NORMALIZED_PHONE
    assert data['tg_id'] == UPDATED_TG_ID


async def test_update_user_password_does_not_return_pass(
    client: AsyncClient,
    db_session: AsyncSession,
    user_payload: dict[str, Any],
    admin_payload: dict[str, Any],
) -> None:
    """При обновлении пароля API не возвращает пароль в ответе."""
    create_response = await client.post(USERS_URL, json=user_payload)
    created_user = create_response.json()
    await create_user_in_db(db_session, admin_payload, role=UserRole.ADMIN)

    headers = await get_auth_headers(client, login=admin_payload['email'])

    response = await client.patch(
        USER_DETAIL_URL.format(user_id=created_user['id']),
        json={'password': UPDATED_USER_PASSWORD},
        headers=headers,
    )

    assert response.status_code == OK_STATUS

    data = response.json()

    assert_public_user_schema(data)
    assert_password_is_not_returned(data)


async def test_update_unknown_user_returns_404(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_payload: dict[str, Any],
) -> None:
    """Попытка обновить пользователя, которого нет."""
    await create_user_in_db(db_session, admin_payload, role=UserRole.ADMIN)
    headers = await get_auth_headers(client, login=admin_payload['email'])

    response = await client.patch(
        USER_DETAIL_URL.format(user_id=UNKNOWN_UUID),
        json={'username': UPDATED_USERNAME},
        headers=headers,
    )

    assert response.status_code == NOT_FOUND_STATUS


async def test_update_user_with_invalid_id_returns_422(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_payload: dict[str, Any],
) -> None:
    """Проверяем ситуацию, когда user_id вообще не UUID."""
    await create_user_in_db(db_session, admin_payload, role=UserRole.ADMIN)
    headers = await get_auth_headers(client, login=admin_payload['email'])

    response = await client.patch(
        USER_DETAIL_URL.format(user_id=INVALID_UUID),
        json={'username': UPDATED_USERNAME},
        headers=headers,
    )

    assert response.status_code == VALIDATION_ERROR_STATUS
