import re

from passlib.context import CryptContext
from pydantic import BaseModel, Field, SecretStr

from schemas.heplers import normalize_phone

from core.constants import EMAIL_REGEX, INVALID_EMAIL, INVALID_PHONE, TOKEN_TYPE

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class AuthData(BaseModel):
    """Схема для ауентификации пользователя."""

    login: str = Field(..., description='Email или номер телефона')
    password: SecretStr = Field(..., description='Пароль')


class TokenResponse(BaseModel):
    """Схема получения ответа с токеном."""

    access_token: str
    token_type: str = TOKEN_TYPE


def get_password_hash(password: str) -> str:
    """Процесс хэширования пароля."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка верности введённого пароля."""
    return pwd_context.verify(plain_password, hashed_password)


def validate_login(login: str) -> str:
    """Проверить логин и привести его к формату хранения."""
    if '@' in login:
        if not re.match(EMAIL_REGEX, login):
            raise ValueError(INVALID_EMAIL)
        return login.lower()

    normalized_phone = normalize_phone(login)
    if normalized_phone is None:
        raise ValueError(INVALID_PHONE)

    return normalized_phone
