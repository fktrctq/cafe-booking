from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserRole
from tests.constants import (
    AUTH_HEADER_NAME,
    BEARER_TOKEN_PREFIX,
    FORBIDDEN_STATUS,
    MALFORMED_TOKEN,
    OK_STATUS,
    UNAUTHORIZED_STATUS,
    UPDATED_USERNAME,
    USERS_ME_URL,
    USERS_URL,
    USER_DETAIL_URL,
)
from tests.helpers import (
    assert_password_is_not_returned,
    assert_public_user_schema,
    create_user,
    create_user_and_get_auth_headers,
    create_user_in_db,
    create_user_with_role_and_get_headers,
    get_auth_headers,
    make_unique_user_payload,
    update_user_role,
)


@pytest.mark.parametrize(
    'method, url',
    [
        ('get', USERS_URL),
        ('get', USER_DETAIL_URL),
        ('patch', USER_DETAIL_URL),
        ('get', USERS_ME_URL),
        ('patch', USERS_ME_URL),
    ],
)
async def test_protected_user_endpoints_without_token_return_401(
    client: AsyncClient,
    user_payload: dict[str, Any],
    method: str,
    url: str,
) -> None:
    """Закрытые user endpoints без токена возвращают 401."""
    created_user = await create_user(client, user_payload)
    endpoint = url.format(user_id=created_user['id'])

    request_kwargs = {}
    if method == 'patch':
        request_kwargs['json'] = {}

    response = await client.request(method.upper(), endpoint, **request_kwargs)

    assert response.status_code == UNAUTHORIZED_STATUS


async def test_protected_user_endpoint_with_invalid_token_returns_401(
    client: AsyncClient,
) -> None:
    """Невалидный JWT не дает доступ к закрытому endpoint."""
    response = await client.get(
        USERS_URL,
        headers={
            AUTH_HEADER_NAME: f'{BEARER_TOKEN_PREFIX} {MALFORMED_TOKEN}',
        },
    )

    assert response.status_code == UNAUTHORIZED_STATUS


async def test_regular_user_can_get_own_profile(
    client: AsyncClient,
    user_payload: dict[str, Any],
) -> None:
    """Обычный авторизованный пользователь может получить /users/me."""
    created_user, headers = await create_user_and_get_auth_headers(
        client,
        user_payload,
    )

    response = await client.get(USERS_ME_URL, headers=headers)

    assert response.status_code == OK_STATUS

    data = response.json()

    assert_public_user_schema(data)
    assert_password_is_not_returned(data)
    assert data['id'] == created_user['id']


async def test_regular_user_can_update_own_profile(
    client: AsyncClient,
    user_payload: dict[str, Any],
) -> None:
    """Обычный авторизованный пользователь может обновить свой профиль."""
    _, headers = await create_user_and_get_auth_headers(client, user_payload)

    response = await client.patch(
        USERS_ME_URL,
        json={'username': UPDATED_USERNAME},
        headers=headers,
    )

    assert response.status_code == OK_STATUS

    data = response.json()

    assert_public_user_schema(data)
    assert_password_is_not_returned(data)
    assert data['username'] == UPDATED_USERNAME


@pytest.mark.parametrize(
    'url',
    [
        USERS_URL,
        USER_DETAIL_URL,
    ],
)
async def test_regular_user_cannot_read_users_data_returns_403(
    client: AsyncClient,
    user_payload: dict[str, Any],
    another_user_payload: dict[str, Any],
    url: str,
) -> None:
    """Обычный USER не может читать список пользователей и чужой профиль."""
    _, headers = await create_user_and_get_auth_headers(client, user_payload)
    another_user = await create_user(client, another_user_payload)
    endpoint = url.format(user_id=another_user['id'])

    response = await client.get(endpoint, headers=headers)

    assert response.status_code == FORBIDDEN_STATUS


async def test_regular_user_cannot_update_another_user_returns_403(
    client: AsyncClient,
    user_payload: dict[str, Any],
    another_user_payload: dict[str, Any],
) -> None:
    """Обычный USER не может обновлять чужой профиль по user_id."""
    _, headers = await create_user_and_get_auth_headers(client, user_payload)
    another_user = await create_user(client, another_user_payload)

    response = await client.patch(
        USER_DETAIL_URL.format(user_id=another_user['id']),
        json={'username': UPDATED_USERNAME},
        headers=headers,
    )

    assert response.status_code == FORBIDDEN_STATUS


@pytest.mark.parametrize(
    'privileged_payload_fixture, role',
    [
        ('admin_payload', UserRole.ADMIN),
        ('manager_payload', UserRole.MANAGER),
    ],
)
async def test_admin_and_manager_can_get_users_list(
    client: AsyncClient,
    db_session: AsyncSession,
    request: pytest.FixtureRequest,
    privileged_payload_fixture: str,
    role: UserRole,
) -> None:
    """ADMIN и MANAGER могут получать список пользователей."""
    privileged_payload = request.getfixturevalue(privileged_payload_fixture)

    await create_user(client, make_unique_user_payload(index=1))
    await create_user(client, make_unique_user_payload(index=2))
    await create_user_in_db(db_session, privileged_payload, role=role)

    headers = await get_auth_headers(
        client,
        login=privileged_payload['email'],
    )

    response = await client.get(USERS_URL, headers=headers)

    assert response.status_code == OK_STATUS
    assert len(response.json()) == 3


@pytest.mark.parametrize(
    'privileged_payload_fixture, role',
    [
        ('admin_payload', UserRole.ADMIN),
        ('manager_payload', UserRole.MANAGER),
    ],
)
async def test_admin_and_manager_can_get_user_by_id(
    client: AsyncClient,
    db_session: AsyncSession,
    request: pytest.FixtureRequest,
    privileged_payload_fixture: str,
    role: UserRole,
) -> None:
    """ADMIN и MANAGER могут получать пользователя по id."""
    target_user = await create_user(client, make_unique_user_payload(index=1))

    privileged_payload = request.getfixturevalue(privileged_payload_fixture)
    await create_user_in_db(db_session, privileged_payload, role=role)

    headers = await get_auth_headers(
        client,
        login=privileged_payload['email'],
    )

    response = await client.get(
        USER_DETAIL_URL.format(user_id=target_user['id']),
        headers=headers,
    )

    assert response.status_code == OK_STATUS

    data = response.json()

    assert_public_user_schema(data)
    assert_password_is_not_returned(data)
    assert data['id'] == target_user['id']


@pytest.mark.parametrize(
    'privileged_payload_fixture, role',
    [
        ('admin_payload', UserRole.ADMIN),
        ('manager_payload', UserRole.MANAGER),
    ],
)
async def test_admin_and_manager_can_update_user_by_id(
    client: AsyncClient,
    db_session: AsyncSession,
    request: pytest.FixtureRequest,
    privileged_payload_fixture: str,
    role: UserRole,
) -> None:
    """ADMIN и MANAGER могут обновлять пользователя по id."""
    target_user = await create_user(client, make_unique_user_payload(index=1))

    privileged_payload = request.getfixturevalue(privileged_payload_fixture)
    await create_user_in_db(db_session, privileged_payload, role=role)

    headers = await get_auth_headers(
        client,
        login=privileged_payload['email'],
    )

    response = await client.patch(
        USER_DETAIL_URL.format(user_id=target_user['id']),
        json={'username': UPDATED_USERNAME},
        headers=headers,
    )

    assert response.status_code == OK_STATUS

    data = response.json()

    assert_public_user_schema(data)
    assert_password_is_not_returned(data)
    assert data['username'] == UPDATED_USERNAME


async def test_admin_cannot_deactivate_self(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_payload: dict[str, Any],
) -> None:
    """Админ не может деактивировать самого себя -> 403."""
    await create_user_in_db(db_session, admin_payload, role=UserRole.ADMIN)
    headers = await get_auth_headers(client, login=admin_payload['email'])

    me = (await client.get(USERS_ME_URL, headers=headers)).json()
    response = await client.patch(
        USER_DETAIL_URL.format(user_id=me['id']),
        json={'is_active': False},
        headers=headers,
    )
    assert response.status_code == FORBIDDEN_STATUS


async def test_manager_cannot_change_is_active(
    client: AsyncClient,
    db_session: AsyncSession,
    manager_payload: dict[str, Any],
) -> None:
    """Менеджер не может менять is_active -> 403."""
    await create_user_in_db(db_session, manager_payload, role=UserRole.MANAGER)
    headers = await get_auth_headers(client, login=manager_payload['email'])
    target = await create_user(client, make_unique_user_payload(index=1))

    response = await client.patch(
        USER_DETAIL_URL.format(user_id=target['id']),
        json={'is_active': False},
        headers=headers,
    )
    assert response.status_code == FORBIDDEN_STATUS


async def test_regular_user_cannot_change_own_role(
    client: AsyncClient,
    user_payload: dict[str, Any],
) -> None:
    """Обычный пользователь не может повысить собственную роль."""
    _, headers = await create_user_and_get_auth_headers(client, user_payload)

    response = await client.patch(
        USERS_ME_URL,
        json={'role': UserRole.ADMIN.value},
        headers=headers,
    )

    assert response.status_code == FORBIDDEN_STATUS


async def test_admin_cannot_change_own_role(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_payload: dict[str, Any],
) -> None:
    """Админ не может изменить собственную роль через /users/me."""
    _, headers = await create_user_with_role_and_get_headers(
        client,
        db_session,
        admin_payload,
        UserRole.ADMIN,
    )

    response = await client.patch(
        USERS_ME_URL,
        json={'role': UserRole.USER.value},
        headers=headers,
    )

    assert response.status_code == FORBIDDEN_STATUS


async def test_admin_cannot_change_own_role_by_id(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_payload: dict[str, Any],
) -> None:
    """Админ не может изменить собственную роль через endpoint по ID."""
    admin, headers = await create_user_with_role_and_get_headers(
        client,
        db_session,
        admin_payload,
        UserRole.ADMIN,
    )

    response = await update_user_role(
        client,
        admin.id,
        UserRole.USER,
        headers,
    )

    assert response.status_code == FORBIDDEN_STATUS


async def test_manager_cannot_change_user_role(
    client: AsyncClient,
    db_session: AsyncSession,
    manager_payload: dict[str, Any],
) -> None:
    """Менеджер не может изменить роль другого пользователя."""
    _, headers = await create_user_with_role_and_get_headers(
        client,
        db_session,
        manager_payload,
        UserRole.MANAGER,
    )
    target_user = await create_user_in_db(
        db_session,
        make_unique_user_payload(index=1),
        role=UserRole.USER,
    )

    response = await update_user_role(
        client,
        target_user.id,
        UserRole.MANAGER,
        headers,
    )

    assert response.status_code == FORBIDDEN_STATUS


async def test_admin_can_change_another_user_role(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_payload: dict[str, Any],
) -> None:
    """Админ может изменить роль другого пользователя ниже себя."""
    admin, headers = await create_user_with_role_and_get_headers(
        client,
        db_session,
        admin_payload,
        UserRole.ADMIN,
    )
    target_user = await create_user_in_db(
        db_session,
        make_unique_user_payload(index=1),
        role=UserRole.USER,
    )

    assert target_user.id != admin.id

    response = await update_user_role(
        client,
        target_user.id,
        UserRole.MANAGER,
        headers,
    )

    assert response.status_code == OK_STATUS
    assert response.json()['role'] == UserRole.MANAGER.value


async def test_admin_can_change_manager_role_to_user(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_payload: dict[str, Any],
) -> None:
    """Админ может понизить менеджера до обычного пользователя."""
    _, headers = await create_user_with_role_and_get_headers(
        client,
        db_session,
        admin_payload,
        UserRole.ADMIN,
    )
    target_user = await create_user_in_db(
        db_session,
        make_unique_user_payload(index=1),
        role=UserRole.MANAGER,
    )

    response = await update_user_role(
        client,
        target_user.id,
        UserRole.USER,
        headers,
    )

    assert response.status_code == OK_STATUS
    assert response.json()['role'] == UserRole.USER.value


async def test_admin_can_change_another_admin_role(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_payload: dict[str, Any],
) -> None:
    """Админ может изменить роль другого админа."""
    _, headers = await create_user_with_role_and_get_headers(
        client,
        db_session,
        admin_payload,
        UserRole.ADMIN,
    )
    target_admin = await create_user_in_db(
        db_session,
        make_unique_user_payload(index=1),
        role=UserRole.ADMIN,
    )

    response = await update_user_role(
        client,
        target_admin.id,
        UserRole.USER,
        headers,
    )

    assert response.status_code == OK_STATUS


async def test_admin_can_grant_admin_role(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_payload: dict[str, Any],
) -> None:
    """Админ может назначить другому пользователю роль ADMIN."""
    _, headers = await create_user_with_role_and_get_headers(
        client,
        db_session,
        admin_payload,
        UserRole.ADMIN,
    )
    target_user = await create_user_in_db(
        db_session,
        make_unique_user_payload(index=1),
        role=UserRole.USER,
    )

    response = await update_user_role(
        client,
        target_user.id,
        UserRole.ADMIN,
        headers,
    )

    assert response.status_code == OK_STATUS
