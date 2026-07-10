from http import HTTPStatus
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from models import User, UserRole

from .security import make_not_authenticated_error
from core.constants import ACCESS_DENIED_ERROR, NOT_AUTHENTICATED_ERROR, TOKEN_FORMAT, TOKEN_TYPE

security_bearer = HTTPBearer(
    bearerFormat=TOKEN_FORMAT,
    scheme_name=TOKEN_TYPE,
    auto_error=False,
)
SecurityBearDep = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(security_bearer),
]  # Только для отображения в UI Swagger


async def get_current_user(request: Request, _: SecurityBearDep) -> User:
    """Получить текущего пользователя из request.state (установлен middleware)."""
    user = getattr(request.state, 'user', None)
    if user is None:
        raise make_not_authenticated_error(NOT_AUTHENTICATED_ERROR)

    return user


async def get_optional_user(request: Request) -> Optional[User]:
    """Получить текущего пользователя или None."""
    return getattr(request.state, 'user', None)


async def get_current_admin_or_manager(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Проверить, что текущий пользователь ADMIN или MANAGER."""
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail=ACCESS_DENIED_ERROR,
        )
    return current_user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentUserOptionalDep = Annotated[Optional[User], Depends(get_optional_user)]
AdminOrManagerDep = Annotated[User, Depends(get_current_admin_or_manager)]
