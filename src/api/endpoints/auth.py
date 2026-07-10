from fastapi import APIRouter, HTTPException, status

from middleware.auth import AuthData, TokenResponse, auth_service, create_access_token

from core.constants import INVALID_CREDENTIALS_ERROR, JWT_SUB_FIELD, TOKEN_TYPE
from core.db import SessionDep

router = APIRouter()


@router.post(
    '/login',
    summary='Получение токена авторизации',
    response_model=TokenResponse,
)
async def auth_user(user_data: AuthData, session: SessionDep) -> TokenResponse:
    """Авторизация и выдача токена."""
    user = await auth_service.authenticate_user(
        session=session,
        login=user_data.login,
        password=user_data.password.get_secret_value(),
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=INVALID_CREDENTIALS_ERROR,
        )

    access_token = create_access_token(data={JWT_SUB_FIELD: str(user.id)})

    return TokenResponse(access_token=access_token, token_type=TOKEN_TYPE)
