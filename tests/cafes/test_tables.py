from http import HTTPStatus

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.api_factories import admin_with_cafe, auth_headers, create_table


async def test_create_table_without_cafe_id_in_body(client: AsyncClient, db_session: AsyncSession) -> None:
    """cafe_id берётся из пути — в теле не нужен."""
    admin, cafe = await admin_with_cafe(client, db_session)
    response = await client.post(
        f'/api/v1/cafes/{cafe["id"]}/tables/',
        json={'seat_number': 4, 'description': 'у окна'},
        headers=admin,
    )
    assert response.status_code == HTTPStatus.CREATED


async def test_table_response_has_nested_cafe(client: AsyncClient, db_session: AsyncSession) -> None:
    """TableInfo содержит вложенный объект cafe."""
    admin, cafe = await admin_with_cafe(client, db_session)
    table = await create_table(client, cafe['id'], admin)
    assert isinstance(table.get('cafe'), dict)
    assert table['cafe']['id'] == cafe['id']


async def test_get_tables_list(client: AsyncClient, db_session: AsyncSession) -> None:
    """Список столов кафе."""
    admin, cafe = await admin_with_cafe(client, db_session)
    await create_table(client, cafe['id'], admin)
    response = await client.get(f'/api/v1/cafes/{cafe["id"]}/tables/', headers=admin)
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()) >= 1


async def test_update_table(client: AsyncClient, db_session: AsyncSession) -> None:
    """Обновление стола."""
    admin, cafe = await admin_with_cafe(client, db_session)
    table = await create_table(client, cafe['id'], admin)
    response = await client.patch(
        f'/api/v1/cafes/{cafe["id"]}/tables/{table["id"]}',
        json={'seat_number': 6},
        headers=admin,
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['seat_number'] == 6


async def test_create_table_forbidden_for_user(client: AsyncClient, db_session: AsyncSession) -> None:
    """Обычный пользователь не может создавать столы -> 403."""
    admin, cafe = await admin_with_cafe(client, db_session)
    user = await auth_headers(client, db_session, index=5, role='USER')
    response = await client.post(
        f'/api/v1/cafes/{cafe["id"]}/tables/',
        json={'seat_number': 2},
        headers=user,
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
