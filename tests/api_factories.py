import base64
from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, UserRole
from tests.helpers import create_user_in_db, get_auth_headers, make_unique_user_payload

PNG_1X1 = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=',
)


async def make_user(
    session: AsyncSession,
    *,
    index: int = 1,
    role: str = 'USER',
    **overrides: Any,
) -> User:
    """Создать пользователя в БД с нужной ролью (регистрация роль не выдаёт)."""
    payload = make_unique_user_payload(index=index, **overrides)
    return await create_user_in_db(session, payload, role=UserRole[role])


async def auth_headers(
    client: AsyncClient,
    session: AsyncSession,
    *,
    index: int = 1,
    role: str = 'USER',
    **overrides: Any,
) -> dict[str, str]:
    """Создать пользователя с ролью в БД и вернуть Authorization-заголовок."""
    payload = make_unique_user_payload(index=index, **overrides)
    await create_user_in_db(session, payload, role=UserRole[role])
    return await get_auth_headers(client, login=payload['email'])


async def create_cafe(
    client: AsyncClient,
    headers: dict[str, str],
    managers_id: list,
    **overrides: Any,
) -> dict[str, Any]:
    """Создать кафе (managers_id обязателен в API develop)."""
    payload = {
        'name': 'Cafe',
        'address': 'Lenina 1',
        'phone': '+79991234567',
        'managers_id': [str(m) for m in managers_id],
    }
    payload.update(overrides)
    response = await client.post('/api/v1/cafes/', json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def create_table(
    client: AsyncClient,
    cafe_id: str,
    headers: dict[str, str],
    **overrides: Any,
) -> dict[str, Any]:
    """Создать стол (cafe_id из пути)."""
    payload = {'seat_number': 4, 'description': 'у окна'}
    payload.update(overrides)
    response = await client.post(f'/api/v1/cafes/{cafe_id}/tables/', json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def create_slot(
    client: AsyncClient,
    cafe_id: str,
    headers: dict[str, str],
    **overrides: Any,
) -> dict[str, Any]:
    """Создать слот (cafe_id из пути)."""
    payload = {'start_time': '18:00:00', 'end_time': '20:00:00', 'description': 'вечер'}
    payload.update(overrides)
    response = await client.post(f'/api/v1/cafes/{cafe_id}/time_slots/', json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def admin_with_cafe(
    client: AsyncClient,
    session: AsyncSession,
    *,
    index_admin: int = 1,
    index_manager: int = 2,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Создать админа, менеджера и кафе. Вернуть (заголовки админа, кафе)."""
    admin = await auth_headers(client, session, index=index_admin, role='ADMIN')
    manager = await make_user(session, index=index_manager, role='MANAGER')
    cafe = await create_cafe(client, admin, [manager.id])
    return admin, cafe
