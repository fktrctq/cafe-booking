from http import HTTPStatus

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.api_factories import admin_with_cafe, create_slot


async def test_create_slot_without_cafe_id_in_body(client: AsyncClient, db_session: AsyncSession) -> None:
    """cafe_id берётся из пути — в теле не нужен."""
    admin, cafe = await admin_with_cafe(client, db_session)
    response = await client.post(
        f'/api/v1/cafes/{cafe["id"]}/time_slots/',
        json={'start_time': '10:00:00', 'end_time': '12:00:00', 'description': 'утро'},
        headers=admin,
    )
    assert response.status_code == HTTPStatus.CREATED


async def test_slot_has_description_and_nested_cafe(client: AsyncClient, db_session: AsyncSession) -> None:
    """Слот хранит description и отдаёт вложенный cafe."""
    admin, cafe = await admin_with_cafe(client, db_session)
    slot = await create_slot(client, cafe['id'], admin, description='ужин')
    assert slot.get('description') == 'ужин'
    assert isinstance(slot.get('cafe'), dict)
    assert slot['cafe']['id'] == cafe['id']


async def test_slot_invalid_time_range(client: AsyncClient, db_session: AsyncSession) -> None:
    """start_time >= end_time -> 422."""
    admin, cafe = await admin_with_cafe(client, db_session)
    response = await client.post(
        f'/api/v1/cafes/{cafe["id"]}/time_slots/',
        json={'start_time': '20:00:00', 'end_time': '18:00:00'},
        headers=admin,
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_update_slot(client: AsyncClient, db_session: AsyncSession) -> None:
    """Обновление слота."""
    admin, cafe = await admin_with_cafe(client, db_session)
    slot = await create_slot(client, cafe['id'], admin)
    response = await client.patch(
        f'/api/v1/cafes/{cafe["id"]}/time_slots/{slot["id"]}',
        json={'description': 'изменено'},
        headers=admin,
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['description'] == 'изменено'
