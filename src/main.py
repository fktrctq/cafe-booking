import logging
import logging.config
import traceback
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from api.routers import main_router
from cache.redis_client import redis_client
from middleware.auth.auth_middleware import AuthMiddleware
from middleware.logging import LoggingMiddleware
from scripts.create_superuser import create_super_user

from core.config import settings
from core.logging_conf import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


openapi_tags = [
    {
        'name': 'Аутентификация',
        'description': 'Вход в систему и получение JWT токена',
    },
    {
        'name': 'Пользователи',
        'description': 'Управление пользователями системы',
    },
    {
        'name': 'Кафе',
        'description': 'Управление кафе и их информацией',
    },
    {
        'name': 'Столы',
        'description': 'Управление столиками в кафе',
    },
    {
        'name': 'Временные слоты',
        'description': 'Управление интервалами бронирования',
    },
    {
        'name': 'Бронирования',
        'description': 'Управление бронированиями столиков',
    },
    {
        'name': 'Медиа',
        'description': 'Управление изображениями',
    },
    {
        'name': 'Celery Beat/Управление расписанием',
        'description': 'Управление расписанием задач/CRUD операции над расписаниями',
    },
    {
        'name': 'Celery Beat/Управление задачами',
        'description': 'Управление периодическими задачами/CRUD операции над задачами',
    },
    {
        'name': 'Health Check',
        'description': 'Проверка работоспособности сервиса и зависимостей',
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Жизненный цикл приложения FastAPI."""
    logger.debug(f'Файл переменных {settings.model_config.get("env_file")}')
    logger.debug(
        f'Создание суперпользователя username:{settings.superuser_name}, адрес:{settings.superuser_email}',
    )
    await create_super_user(settings.superuser_email, settings.superuser_name, settings.superuser_password)
    await redis_client.connect()
    yield
    await redis_client.disconnect()


app = FastAPI(
    openapi_tags=openapi_tags,
    title=settings.app_title,
    version=settings.version,
    description=settings.app_descriptions,
    contact={'Author': settings.app_author},
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Обработчик HTTP исключений."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'code': exc.status_code,
            'message': exc.detail,
        },
    )


@app.exception_handler(ValidationError)
@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Обработчик ошибок валидации запроса."""
    errors = exc.errors()
    if not errors:
        message = 'Ошибка валидации данных'
    else:
        first_error = errors[0]
        if first_error['type'] == 'value_error':
            message = first_error['msg'].replace('Value error, ', '')
        else:
            field = first_error['loc'][-1]
            message = f'{field}: {first_error["msg"]}'

    return JSONResponse(
        status_code=422,
        content={
            'code': 422,
            'message': message,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для непредвиденных ошибок."""
    logger.error(f'Внутренняя ошибка сервера: {exc}')
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'message': 'Внутренняя ошибка сервера',
        },
    )


app.add_middleware(LoggingMiddleware, log_level='INFO')
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allow_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(main_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
