from http import HTTPStatus

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.api_factories import auth_headers, create_cafe, make_user

CAFE_PAYLOAD = {'name': 'My Cafe', 'address': 'Lenina 1', 'phone': '+79991234567'}


async def test_create_cafe_as_admin(client: AsyncClient, db_session: AsyncSession) -> None:
    """Админ создаёт кафе -> 201."""
    admin = await auth_headers(client, db_session, index=1, role='ADMIN')
    manager = await make_user(db_session, index=2, role='MANAGER')
    response = await client.post(
        '/api/v1/cafes/',
        json={**CAFE_PAYLOAD, 'managers_id': [str(manager.id)]},
        headers=admin,
    )
    assert response.status_code == HTTPStatus.CREATED


async def test_create_cafe_requires_auth(client: AsyncClient, db_session: AsyncSession) -> None:
    """Без токена создать кафе нельзя -> 401."""
    manager = await make_user(db_session, index=2, role='MANAGER')
    response = await client.post(
        '/api/v1/cafes/',
        json={**CAFE_PAYLOAD, 'managers_id': [str(manager.id)]},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_create_cafe_forbidden_for_user(client: AsyncClient, db_session: AsyncSession) -> None:
    """Обычный пользователь не может создать кафе -> 403."""
    user = await auth_headers(client, db_session, index=1, role='USER')
    manager = await make_user(db_session, index=2, role='MANAGER')
    response = await client.post(
        '/api/v1/cafes/',
        json={**CAFE_PAYLOAD, 'managers_id': [str(manager.id)]},
        headers=user,
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


async def test_get_cafe_by_id(client: AsyncClient, db_session: AsyncSession) -> None:
    """Получение кафе по id."""
    admin = await auth_headers(client, db_session, index=1, role='ADMIN')
    manager = await make_user(db_session, index=2, role='MANAGER')
    cafe = await create_cafe(client, admin, [manager.id])
    response = await client.get(f'/api/v1/cafes/{cafe["id"]}', headers=admin)
    assert response.status_code == HTTPStatus.OK
    assert response.json()['id'] == cafe['id']


async def test_update_cafe_as_admin(client: AsyncClient, db_session: AsyncSession) -> None:
    """Обновление кафе администратором."""
    admin = await auth_headers(client, db_session, index=1, role='ADMIN')
    manager = await make_user(db_session, index=2, role='MANAGER')
    cafe = await create_cafe(client, admin, [manager.id])
    response = await client.patch(
        f'/api/v1/cafes/{cafe["id"]}',
        json={'description': 'обновлено'},
        headers=admin,
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['description'] == 'обновлено'


async def test_create_cafe_with_managers(client: AsyncClient, db_session: AsyncSession) -> None:
    """Кафе создаётся с менеджерами."""
    admin = await auth_headers(client, db_session, index=1, role='ADMIN')
    manager = await make_user(db_session, index=2, role='MANAGER')
    response = await client.post(
        '/api/v1/cafes/',
        json={**CAFE_PAYLOAD, 'managers_id': [str(manager.id)]},
        headers=admin,
    )
    assert response.status_code == HTTPStatus.CREATED
    assert str(manager.id) in [m['id'] for m in response.json()['managers']]
