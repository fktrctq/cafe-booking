from datetime import date, timedelta
from http import HTTPStatus
from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.api_factories import admin_with_cafe, auth_headers, create_slot, create_table

FUTURE_DATE = str(date.today() + timedelta(days=10))
PAST_DATE = str(date.today() - timedelta(days=1))


async def _prepare(
    client: AsyncClient,
    session: AsyncSession,
) -> tuple[dict[str, str], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Создать админа+кафе, пользователя, стол и слот."""
    admin, cafe = await admin_with_cafe(client, session, index_admin=1, index_manager=2)
    user = await auth_headers(client, session, index=3, role='USER')
    table = await create_table(client, cafe['id'], admin)
    slot = await create_slot(client, cafe['id'], admin)
    return user, cafe, table, slot


def _booking_payload(
    cafe: dict[str, Any],
    table: dict[str, Any],
    slot: dict[str, Any],
    booking_date: str = FUTURE_DATE,
) -> dict[str, Any]:
    return {
        'cafe_id': cafe['id'],
        'tables_slots': [{'table_id': table['id'], 'slot_id': slot['id']}],
        'guest_number': 2,
        'booking_date': booking_date,
        'note': 'у окна',
    }


async def test_create_booking_sets_current_user(client: AsyncClient, db_session: AsyncSession) -> None:
    """Бронь создаётся, user берётся из токена -> 201."""
    user, cafe, table, slot = await _prepare(client, db_session)
    response = await client.post(
        '/api/v1/booking/',
        json=_booking_payload(cafe, table, slot),
        headers=user,
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['user']['id']


async def test_create_booking_requires_auth(client: AsyncClient, db_session: AsyncSession) -> None:
    """Без токена бронь нельзя -> 401."""
    _, cafe, table, slot = await _prepare(client, db_session)
    response = await client.post(
        '/api/v1/booking/',
        json=_booking_payload(cafe, table, slot),
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_booking_past_date_rejected(client: AsyncClient, db_session: AsyncSession) -> None:
    """Бронь на прошедшую дату -> 400/422."""
    user, cafe, table, slot = await _prepare(client, db_session)
    response = await client.post(
        '/api/v1/booking/',
        json=_booking_payload(cafe, table, slot, booking_date=PAST_DATE),
        headers=user,
    )
    assert response.status_code in (HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY)


async def test_user_sees_only_own_bookings(client: AsyncClient, db_session: AsyncSession) -> None:
    """Пользователь в списке видит только свои брони."""
    user, cafe, table, slot = await _prepare(client, db_session)
    await client.post(
        '/api/v1/booking/',
        json=_booking_payload(cafe, table, slot),
        headers=user,
    )
    other = await auth_headers(client, db_session, index=7, role='USER')
    response = await client.get('/api/v1/booking/', headers=other)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == []


async def test_user_bookings_must_not_overlap(client: AsyncClient, db_session: AsyncSession) -> None:
    """Две брони пользователя с пересекающимся временем (разные столы) -> 400."""
    user, cafe, table, slot = await _prepare(client, db_session)
    admin = await auth_headers(client, db_session, index=10, role='ADMIN')
    table2 = await create_table(client, cafe['id'], admin)

    first = await client.post(
        '/api/v1/booking/',
        json=_booking_payload(cafe, table, slot),
        headers=user,
    )
    assert first.status_code == HTTPStatus.CREATED

    second = await client.post(
        '/api/v1/booking/',
        json=_booking_payload(cafe, table2, slot),
        headers=user,
    )
    assert second.status_code == HTTPStatus.BAD_REQUEST
