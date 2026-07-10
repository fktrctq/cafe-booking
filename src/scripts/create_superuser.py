import argparse
import asyncio
import logging
import logging.config
from typing import Optional

from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.auth.password import get_password_hash
from models import User, UserRole
from schemas.user import UserCreate

from core.db import AsyncSessionLocal
from core.logging_conf import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


async def _create_super_user(username: str, email: str, password: str, session: AsyncSession) -> User:
    """Создать пользователя."""
    user = User(
        username=username,
        email=email,
        password=get_password_hash(password),
        role=UserRole.ADMIN,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _find_user(username: str, email: str, session: AsyncSession) -> Optional[User]:
    """Поиск пользователя по username и email."""
    query = select(User).where(or_(User.username == username, User.email == email))
    result = await session.execute(query)
    return result.scalar()


async def _validate_user(username: str, email: str, password: str) -> Optional[UserCreate]:
    """Валидирует поля для пользователя."""
    try:
        return UserCreate(
            username=username,
            email=email,
            password=password,
        )

    except ValidationError as error:
        logger.error(f'Ошибка валидации данных пользователя: {error}')
        return None


async def create_super_user(email: str, username: str, password: str) -> bool:
    """Функция проверки и создания суперпользоателя."""
    async with AsyncSessionLocal() as session:
        try:
            if not all((email, username, password)):
                logger.warning('Недопустимы пустые значения полей: "username", "email", "password"')
                return False

            user_data = await _validate_user(username, email, password)
            if user_data is None:
                return False

            user = await _find_user(user_data.username, user_data.email, session)
            if user:
                logger.warning(
                    f'Ошибка создания суперпользователя "{user_data.username}" с адресом "{user_data.email}"',
                )
                logger.warning(f'Пользователь "{user.username}" с адресом "{user.email}" уже существует')
                return True

            user = await _create_super_user(user_data.username, user_data.email, user_data.password, session)
            logger.info(f'Суперпользователь "{user.username}" с адресом "{user.email}" создан')
            return True

        except SQLAlchemyError as error:
            logger.error(f'Ошибка БД при создании пользователя: {error}')
            await session.rollback()
            return False

        except Exception as error:
            logger.critical(f'Непредвиденная ошибка: {error}', exc_info=True)
            await session.rollback()
            return False
        finally:
            await session.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Создание суперпользователя')
    parser.add_argument('--email', '-l', type=str, required=True, help='Email пользователя')
    parser.add_argument('--username', '-u', type=str, required=True, help='Имя пользователя')
    parser.add_argument('--password', '-p', type=str, required=True, help='Пароль пользователя')
    args = parser.parse_args()
    asyncio.run(create_super_user(email=args.email, username=args.username, password=args.password))
