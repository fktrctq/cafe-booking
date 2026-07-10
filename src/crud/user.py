from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from middleware.auth.password import get_password_hash
from models import User
from schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD для модели User."""

    async def create(self, obj_in: UserCreate, session: AsyncSession) -> User:
        """Создать пользователя с хешированным паролем."""
        user_data = obj_in.model_dump(exclude_unset=True)
        user_data['password'] = get_password_hash(user_data['password'])

        db_obj = self.model(**user_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: User,
        obj_in: UserUpdate,
        session: AsyncSession,
    ) -> User:
        """Обновить пользователя с хешированием нового пароля."""
        user_data = obj_in.model_dump(exclude_unset=True)

        if 'password' in user_data:
            user_data['password'] = get_password_hash(user_data['password'])

        for field, value in user_data.items():
            setattr(db_obj, field, value)

        await session.commit()
        await session.refresh(db_obj)
        return db_obj


user_crud = CRUDUser(User)
