import argparse
import asyncio
import json
import logging
import logging.config
import random
import string
from typing import Any
from datetime import date, time
from pathlib import Path
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from middleware.auth.password import get_password_hash
from models import Booking, BookingStatus, Cafe, Slot, Table, User, UserRole, BookingTableSlot

from core.db import AsyncSessionLocal
from core.logging_conf import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).parent


async def truncate_all_tables(session: AsyncSession) -> None:
    """Очищает все таблицы в правильном порядке (с учётом зависимостей)."""
    # Отключаем проверку внешних ключей
    await session.execute(text("SET session_replication_role = 'replica';"))

    await session.execute(text('TRUNCATE TABLE bookings CASCADE;'))
    await session.execute(text('TRUNCATE TABLE managers_cafes CASCADE;'))
    await session.execute(text('TRUNCATE TABLE slots CASCADE;'))
    await session.execute(text('TRUNCATE TABLE tables CASCADE;'))
    await session.execute(text('TRUNCATE TABLE cafes CASCADE;'))
    await session.execute(text('TRUNCATE TABLE users CASCADE;'))

    # Включаем проверку внешних ключей
    await session.execute(text("SET session_replication_role = 'origin';"))
    await session.commit()

    logger.info('✅ Все таблицы очищены')


def load_json(filename: str) -> list[dict]:
    """Загружает данные из JSON-файла."""
    file_path = FIXTURES_DIR / filename
    logger.info(f'🔍 Загрузка файла: {file_path}')
    if not file_path.exists():
        logger.error(f'❌ Файл не найден: {file_path}')
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    key = Path(filename).stem
    return data.get(key, [])


def generate_password(length: int = 8) -> str:
    """Генерирует случайный пароль."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))


async def upsert_users(session: AsyncSession, data: list[dict]) -> list[dict]:
    """Обновляет или создаёт пользователей."""
    logger.info(f'🔧 upsert_users: начато, получено {len(data)} записей')
    users_list = []  # Список для результатов

    for item in data:
        logger.debug(f'Обработка: {item.get("username")}')
        stmt = select(User).where(User.username == item['username'])
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.username = item.get('username')
            existing.email = item.get('email')
            existing.phone = item.get('phone')
            existing.tg_id = item.get('tg_id')
            existing.role = UserRole(item.get('role', 'USER'))
            existing.is_active = item.get('active', True)
            logger.debug(f'Обновлён пользователь {existing.id}')

            # Добавляем в список результат
            users_list.append({
                'id': str(existing.id),
                'username': existing.username,
                'passord': existing.password,
                'email': existing.email,
                'phone': existing.phone,
                'role': existing.role.value,
                'active': existing.is_active,
            })
        else:
            passwort_user = generate_password()
            user = User(
                username=item.get('username'),
                email=item.get('email'),
                phone=item.get('phone'),
                password=get_password_hash(passwort_user),
                tg_id=item.get('tg_id', None),
                role=UserRole(item.get('role', 'USER')),
                is_active=True,
            )
            session.add(user)
            await session.flush()
            logger.debug(f'Добавлен пользователь {user.id}')

            # Добавляем в список результат
            users_list.append({
                'id': str(user.id),
                'username': user.username,
                'password': passwort_user,
                'email': user.email,
                'phone': user.phone,
                'role': user.role.value,
                'active': user.is_active,
            })

    await session.commit()
    logger.info(f'Загружено/обновлено {len(data)} пользователей.')

    return users_list


async def upsert_cafes(session: AsyncSession, data: list[dict], data_users: list[dict]) -> list[dict]:
    """Обновляет или создаёт кафе."""
    # Список менеджеров из списка пользователей
    managers = [user for user in data_users if user['role'] == 'MANAGER']
    cafe_list = []
    for item in data:
        stmt = select(Cafe).where(Cafe.name == item['name'])  # убрал пробел
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = item.get('name')
            existing.address = item.get('address')
            existing.phone = item.get('phone')
            existing.description = item.get('description', 'Описание кафе')
            existing.photo_id = item.get('photo_id')
            existing.is_active = True
            logger.debug(f'Обновлено кафе {existing.name} ID {existing.id}')
            cafe_list.append({
                'id': str(existing.id),
                'name': existing.name,
                'phone': existing.phone,
                'description ': existing.description,
                'active': existing.is_active,
            })
        else:
            # Выбираем случайного менеджера
            random_manager = random.choice(managers)
            # Получаем объект User по ID
            manager_obj = await session.get(User, random_manager['id'])

            cafe = Cafe(
                name=item['name'],
                address=item['address'],
                phone=item['phone'],
                description=item.get('description', 'Описание кафе'),
                photo_id=item.get('photo_id'),
                is_active=True,
                managers=[manager_obj],  # список объектов User
            )
            session.add(cafe)
            await session.flush()
            cafe_list.append({
                'id': str(cafe.id),
                'name': cafe.name,
                'phone': cafe.phone,
                'description ': cafe.description,
                'active': cafe.is_active,
                'managers': cafe.managers,
            })
            logger.debug(f'Добавлено кафе {cafe.name} с менеджером {random_manager["username"]}')

    await session.commit()
    logger.info(f'Загружено/обновлено {len(cafe_list)} кафе.')
    return cafe_list


async def upsert_tables(session: AsyncSession, data: list[dict], cafe_data: list[dict]) -> list[dict]:
    """Обновляет или создаёт столы для каждого кафе."""
    tables_list = []

    for cafe in cafe_data:
        cafe_id = cafe['id']

        for table_template in data:
            # Ищем существующий стол
            stmt = select(Table).where(
                Table.cafe_id == cafe_id,
                Table.seat_number == table_template['seat_number'],
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.description = table_template.get('description')
                existing.is_active = table_template.get('active', True)
                await session.flush()
                logger.debug(f'Обновлён стол {existing.id} в кафе {cafe_id}')

                tables_list.append({
                    'id': str(existing.id),
                    'cafe_id': str(existing.cafe_id),
                    'cafe_name': cafe.get('name'),
                    'seat_number': existing.seat_number,
                    'description': existing.description,
                    'active': existing.is_active,
                })
            else:
                table = Table(
                    cafe_id=cafe_id,
                    seat_number=table_template['seat_number'],
                    description=table_template.get('description'),
                    is_active=table_template.get('active', True),
                )
                session.add(table)
                await session.flush()
                logger.debug(f'Добавлен стол {table.id} в кафе {cafe_id}')

                tables_list.append({
                    'id': str(table.id),
                    'cafe_id': str(table.cafe_id),
                    'cafe_name': cafe.get('name'),
                    'seat_number': table.seat_number,
                    'description': table.description,
                    'active': table.is_active,
                })

    await session.commit()
    logger.info(f'Обработано столов: {len(tables_list)} для {len(cafe_data)} кафе')

    return tables_list


async def upsert_slots(session: AsyncSession, data: list[dict], cafe_data: list[dict]) -> list[dict]:
    """Обновляет или создаёт слоты для каждого кафе."""
    slots_list = []

    for cafe in cafe_data:
        cafe_id = cafe['id']

        for slot_template in data:
            # Ищем существующий слот
            start_time = time.fromisoformat(slot_template['start_time'])
            end_time = time.fromisoformat(slot_template['end_time'])
            stmt = select(Slot).where(
                Slot.cafe_id == cafe_id,
                Slot.start_time == start_time,
                Slot.end_time == end_time,
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.is_active = slot_template.get('active', True)
                logger.debug(f'Обновлен слот {existing.id} в кафе {cafe_id} active {existing.is_active}')
                await session.flush()
                slots_list.append({
                    'id': str(existing.id),
                    'cafe_id': str(existing.cafe_id),
                    'cafe_name': cafe.get('name'),
                    'start_time': str(existing.start_time),
                    'end_time': str(existing.end_time),
                    'active': existing.is_active,
                })
            else:
                slot = Slot(
                    cafe_id=cafe_id,
                    start_time=start_time,
                    end_time=end_time,
                    is_active=slot_template.get('active', True),
                )
                session.add(slot)
                await session.flush()
                logger.debug(f'Добавлен слот {slot.id} в кафе {cafe_id}')
                slots_list.append({
                    'id': str(slot.id),
                    'cafe_id': str(slot.cafe_id),
                    'cafe_name': cafe.get('name'),
                    'start_time': str(slot.start_time),
                    'end_time': str(slot.end_time),
                    'active': slot.is_active,
                })

    await session.commit()
    logger.info(f'Обработано слотов: {len(slots_list)} для {len(cafe_data)} кафе')

    return slots_list


import random
from datetime import date, timedelta


def generate_bookings(
    users_list: list[dict],
    cafes_list: list[dict],
    tables_list: list[dict],
    slots_list: list[dict],
    days_ahead: int = 10,
    bookings_per_day: int = 10,
) -> list[dict]:
    """Генерирует бронирования на основе существующих данных.

    Args:
        users_list: список пользователей
        cafes_list: список кафе
        tables_list: список столов
        slots_list: список слотов
        days_ahead: на сколько дней вперёд
        bookings_per_day: сколько бронирований в день

    Returns:
        list[dict]: список бронирований

    """
    # Фильтруем только обычных пользователей (USER)
    role_users = [user for user in users_list if user['role'] == 'USER']
    # Группируем столы и слоты по cafe_id для быстрого доступа
    tables_by_cafe = {}
    for table in tables_list:
        cafe_id = table['cafe_id']
        if cafe_id not in tables_by_cafe:
            tables_by_cafe[cafe_id] = []
        tables_by_cafe[cafe_id].append(table)

    slots_by_cafe = {}
    for slot in slots_list:
        cafe_id = slot['cafe_id']
        if cafe_id not in slots_by_cafe:
            slots_by_cafe[cafe_id] = []
        slots_by_cafe[cafe_id].append(slot)

    notes = [
        None,
        'Хотелось бы столик у окна',
        'День рождения',
        'Вегетарианское меню',
        'VIP клиент',
        'Детский стульчик нужен',
        'Особое мероприятие',
        'Свадьба',
        'Юбилей',
        'ЗаБухич',
    ]
    bookings = []
    start_date = date.today()
    now_time = datetime.now().time().replace(second=0, microsecond=0)
    for day_offset in range(days_ahead):
        current_date = start_date + timedelta(days=day_offset)

        for _ in range(bookings_per_day):
            # Выбираем случайного пользователя
            user = random.choice(role_users)

            # Выбираем случайное кафе
            cafe = random.choice(cafes_list)
            cafe_id = cafe['id']

            # Получаем столы и слоты для этого кафе
            cafe_tables = tables_by_cafe.get(cafe_id, [])
            cafe_slots = slots_by_cafe.get(cafe_id, [])

            if not cafe_tables or not cafe_slots:
                continue

            # Выбираем случайный стол и слот
            table = random.choice(cafe_tables)

            if start_date == current_date:
                future_slots = [
                    slot for slot in cafe_slots
                    if time().fromisoformat(slot['start_time']) > now_time
                ]
                if not future_slots:
                    continue
                slot = random.choice(future_slots)
            else:
                slot = random.choice(cafe_slots)
            booking = {
                'user_id': user['id'],
                'cafe_id': cafe_id,
                'cafe_name': slot.get('cafe_name'),
                'table_id': table['id'],
                'table_number': table.get('seat_number'),
                'slot_id': slot['id'],
                'slot_start_time': slot['start_time'],
                'date': current_date.isoformat(),
                'status': 'BOOKING',
                'note': random.choice(notes),
                'is_active': True,
            }
            bookings.append(booking)

    return bookings


async def is_table_available(
    session: AsyncSession,
    table_id: Any,
    slot_id: Any,
    booking_date: date,
) -> Booking | None:
    """Возвращает BookingTableSlot или None."""
    stmt = (
        select(Booking)
        .join(BookingTableSlot)
        .where(
            BookingTableSlot.table_id == table_id,
            BookingTableSlot.slot_id == slot_id,
            Booking.booking_date == booking_date,
            Booking.status.in_([BookingStatus.BOOKING, BookingStatus.ACTIVE])
        )
    )
    result = await session.execute(stmt)
    return result.scalar()

async def upsert_bookings(session: AsyncSession, data: list[dict]) -> list[dict]:
    """Создаёт бронирования."""
    bookings_list = []

    for item in data:
        # # Проверяем, нет ли уже такого бронирования
        booking_date = date.fromisoformat(item['date'])
        booking = await is_table_available(session, item['table_id'], item['slot_id'], booking_date)
        if booking:
            logger.debug(
                f'Бронирование уже существует. Кафе {item.get('cafe_name')} дата {booking.booking_date.isoformat()} '
                f'время {item.get('slot_start_time')} стол {item.get('table_number')}'
                f''
            )
            continue

        # Создаём новое бронирование
        booking = Booking(
            user_id=item['user_id'],
            cafe_id=item['cafe_id'],
            booking_date=booking_date,
            guest_number=random.randint(1, 6),
            status=BookingStatus(item['status']),
            note=item.get('note'),
            is_active=item.get('is_active', True),
        )
        session.add(booking)
        # создаем связь бронирование -> стол+слот
        await session.flush()
        tables_slot = BookingTableSlot(
                table_id=item['table_id'],
                slot_id=item['slot_id'],
                booking_id=booking.id,
            )
        session.add(tables_slot)
        await session.flush()

        logger.debug(
            f'Бронирование добавлено. Кафе {item.get('cafe_name')} дата {booking.booking_date.isoformat()} '
            f'Время {item.get('slot_start_time')} '
            f'стол {item.get('table_number')}, гости {booking.guest_number}'
        )
        bookings_list.append({
            'id': str(booking.id),
            'user_id': str(booking.user_id),
            'cafe_id': str(booking.cafe_id),
            'table_id': str(tables_slot.table_id),
            'slot_id': str(tables_slot.slot_id),
            'slot_start_time': item.get('slot_start_time'),
            'date': booking.booking_date.isoformat(),
            'status': booking.status.value,
            'note': booking.note,
            'active': booking.is_active,
            'guest_number': booking.guest_number,
        })

    await session.commit()
    logger.info(f'Создано бронирований: {len(bookings_list)}')

    return bookings_list


async def main(truncate: bool, iterations: int) -> None:
    """Основная функция загрузки фикстур."""
    async with AsyncSessionLocal() as session:
        if truncate:
            logger.info('🧹 Начало очистки таблиц...')
            await truncate_all_tables(session)
            logger.info('✅ Очистка таблиц успешно завершена')
        else:
            logger.info('🚀 Начало загрузки фикстур...')

            logger.info('📝 Загрузка пользователей...')
            user_data = await upsert_users(session, load_json('example/users.json'))

            logger.info('🏢 Загрузка кафе...')
            cafe_data = await upsert_cafes(session, load_json('example/cafe.json'), user_data)

            logger.info('🪑 Загрузка столов...')
            tables_data = await upsert_tables(session, load_json('example/tables.json'), cafe_data)

            logger.info('⏰ Загрузка слотов...')
            slots_data = await upsert_slots(session, load_json('example/slots.json'), cafe_data)

            logger.info('📅 Генерация и загрузка бронирований...')
            for _ in range(iterations):
                gen_bookings = generate_bookings(user_data, cafe_data, tables_data, slots_data)
                booking_data = await upsert_bookings(session, gen_bookings)
            logger.info('🎉 Загрузка фикстур успешно завершена!')
            for user in user_data:
                logger.info(f' Пользователь: {user.get('username')} логин {user.get('email')} пароль: {user.get('password')}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Загрузка фикстур')
    parser.add_argument('--truncate', action='store_true', default=False,
                         help='Очистить таблицы перед загрузкой')
    parser.add_argument('--iterations', '-i', type=int, default=3,
                       help='Количество итераций генерации бронирований (по умолчанию: 3)')
    args = parser.parse_args()

    asyncio.run(main(truncate=args.truncate, iterations=args.iterations))
