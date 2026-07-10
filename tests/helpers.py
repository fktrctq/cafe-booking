from typing import Any
from uuid import UUID

from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from crud.user import user_crud
from models import User, UserRole
from schemas.user import UserCreate
from tests.constants import (
    AUTH_HEADER_NAME,
    AUTH_LOGIN_URL,
    AUTH_TOKEN_FIELD,
    BEARER_TOKEN_PREFIX,
    CREATED_STATUS,
    EMAIL,
    OK_STATUS,
    PASSWORD_FIELD,
    PHONE,
    PUBLIC_USER_FIELDS,
    TG_ID,
    USERS_URL,
    USER_DETAIL_URL,
    USER_NAME,
    VALID_USER_PASSWORD,
)


def make_user_payload(**overrides: Any) -> dict[str, Any]:
    """Собрать валидный payload для создания пользователя."""
    payload = {
        'username': USER_NAME,
        'email': EMAIL,
        'phone': PHONE,
        'tg_id': TG_ID,
        'password': VALID_USER_PASSWORD,
    }
    payload.update(overrides)
    return payload


def make_unique_user_payload(index: int = 1, **overrides: Any) -> dict[str, Any]:
    """Собрать уникальный payload пользователя для тестов с несколькими users."""
    payload = {
        'username': f'user_{index}',
        'email': f'user_{index}@example.com',
        'phone': f'91234567{index:02d}',
        'tg_id': str(100000000 + index),
        'password': VALID_USER_PASSWORD,
    }
    payload.update(overrides)
    return payload


async def create_user(
    client: AsyncClient,
    payload: dict[str, Any] | None = None,
    expected_status: int = CREATED_STATUS,
) -> dict[str, Any]:
    """Создать пользователя через API и вернуть JSON ответа."""
    if payload is None:
        payload = make_user_payload()

    response = await client.post(USERS_URL, json=payload)
    assert response.status_code == expected_status
    return response.json()


async def create_user_response(
    client: AsyncClient,
    payload: dict[str, Any] | None = None,
) -> Response:
    """Создать пользователя через API и вернуть полный response."""
    if payload is None:
        payload = make_user_payload()
    user_payload = payload or make_user_payload()
    return await client.post(USERS_URL, json=user_payload)


def assert_public_user_schema(user_data: dict[str, Any]) -> None:
    """Проверить, что ответ пользователя содержит публичные поля."""
    assert set(user_data.keys()) == PUBLIC_USER_FIELDS


def assert_password_is_not_returned(user_data: dict[str, Any]) -> None:
    """Проверить, что password не возвращается наружу."""
    assert PASSWORD_FIELD not in user_data


def assert_user_matches_payload(
    user_data: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    """Проверить, что публичные поля пользователя совпадают с payload."""
    assert user_data['username'] == payload['username']
    assert user_data['email'] == payload['email']
    assert user_data['tg_id'] == payload['tg_id']


def make_login_payload(
    login: str,
    password: str = VALID_USER_PASSWORD,
) -> dict[str, str]:
    """Собрать payload для авторизации пользователя."""
    return {
        'login': login,
        'password': password,
    }


async def login_user(
    client: AsyncClient,
    login: str,
    password: str = VALID_USER_PASSWORD,
    expected_status: int = OK_STATUS,
) -> dict[str, Any]:
    """Авторизовать пользователя и вернуть JSON ответа."""
    response = await client.post(
        AUTH_LOGIN_URL,
        json=make_login_payload(login=login, password=password),
    )
    assert response.status_code == expected_status
    return response.json()


async def get_auth_headers(
    client: AsyncClient,
    login: str,
    password: str = VALID_USER_PASSWORD,
) -> dict[str, str]:
    """Получить Authorization headers для авторизованного пользователя."""
    token_data = await login_user(
        client,
        login=login,
        password=password,
    )
    return {
        AUTH_HEADER_NAME: (f'{BEARER_TOKEN_PREFIX} {token_data[AUTH_TOKEN_FIELD]}'),
    }


async def create_user_and_get_auth_headers(
    client: AsyncClient,
    payload: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Создать пользователя и вернуть пару: созданный user + auth headers."""
    if payload is None:
        payload = make_user_payload()

    user_payload = payload or make_user_payload()
    created_user = await create_user(client, user_payload)
    headers = await get_auth_headers(client, login=user_payload['email'])
    return created_user, headers


async def create_user_in_db(
    session: AsyncSession,
    payload: dict[str, Any],
    role: UserRole = UserRole.USER,
) -> User:
    """Создать пользователя в БД с нужной ролью."""
    payload = payload.copy()
    payload.pop('role', None)

    user = await user_crud.create(UserCreate(**payload), session)

    if user.role != role:
        user.role = role
        await session.commit()
        await session.refresh(user)

    return user


async def create_user_with_role_and_get_headers(
    client: AsyncClient,
    session: AsyncSession,
    payload: dict[str, Any],
    role: UserRole,
) -> tuple[User, dict[str, str]]:
    """Создать пользователя с ролью и вернуть auth headers."""
    user = await create_user_in_db(session, payload, role=role)
    headers = await get_auth_headers(client, login=payload['email'])
    return user, headers


async def update_user_role(
    client: AsyncClient,
    user_id: UUID | str,
    role: UserRole,
    headers: dict[str, str],
) -> Response:
    """Отправить PATCH-запрос на изменение роли пользователя."""
    return await client.patch(
        USER_DETAIL_URL.format(user_id=user_id),
        json={'role': role.value},
        headers=headers,
    )
