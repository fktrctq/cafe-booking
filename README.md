# Cafe Booking System

API-сервис для бронирования столиков в кафе.

Проект реализован на **FastAPI** и предоставляет REST API для работы с пользователями, кафе, столами, временными слотами, бронированиями и медиафайлами. Документация API хранится в директории `openapi-docs`.

## Содержание

- [Стек технологий](#стек-технологий)
- [Возможности проекта](#возможности-проекта)
- [Документация API](#документация-api)
- [Основные эндпоинты](#основные-эндпоинты)
- [Переменные окружения](#переменные-окружения)
- [Запуск проекта](#запуск-проекта)
- [Работа через DevContainer](#работа-через-devcontainer)
- [Миграции](#миграции)
- [Фикстуры](#фикстуры)
- [Тесты](#тесты)
- [Структура проекта](#структура-проекта)
- [Авторизация](#авторизация)
- [Celery, RabbitMQ и Flower](#celery-rabbitmq-и-flower)
- [Линтеры и pre-commit](#линтеры-и-pre-commit)

## Стек технологий

- Python 3.12
- FastAPI
- SQLAlchemy Async
- Alembic
- PostgreSQL
- Pydantic
- JWT-аутентификация
- RabbitMQ
- Celery
- Flower
- Pytest
- Ruff
- Pre-commit
- uv
- Docker / Docker Compose
- Dev Containers for VSCode

## Возможности проекта

- регистрация пользователей;
- авторизация через JWT-токен;
- роли пользователей: `USER`, `MANAGER`, `ADMIN`;
- просмотр и обновление профиля текущего пользователя;
- просмотр и управление пользователями для администраторов и менеджеров;
- CRUD-операции для кафе;
- CRUD-операции для столиков внутри кафе;
- CRUD-операции для временных слотов;
- создание и управление бронированиями;
- загрузка изображений с конвертацией в JPG;
- получение медиафайлов по ID;
- проверка состояния приложения через health-check;
- фоновые задачи через Celery;
- мониторинг Celery через Flower.

## Документация API

OpenAPI-документация находится в директории:

```text
openapi-docs/
```

Основная спецификация API:

```text
openapi-docs/docs/openapi.yml
```

Для просмотра документации можно запустить отдельный контейнер:

```bash
cd openapi-docs
docker compose up -d
```

После запуска документация будет доступна по адресам:

```text
http://localhost:8080/index_swagger.html
http://localhost:8080/index_redoc.html
```

## Основные эндпоинты

Базовый URL API:

```text
http://localhost:8000
```

### Аутентификация

```text
POST /auth/login
```

### Пользователи

```text
POST  /users/
GET   /users/
GET   /users/{user_id}
PATCH /users/{user_id}
GET   /users/me
PATCH /users/me
```

### Кафе

```text
GET   /cafes/
POST  /cafes/
GET   /cafes/{cafe_id}
PATCH /cafes/{cafe_id}
```

### Столы

```text
GET   /cafes/{cafe_id}/tables/
POST  /cafes/{cafe_id}/tables/
GET   /cafes/{cafe_id}/tables/{table_id}
PATCH /cafes/{cafe_id}/tables/{table_id}
```

### Временные слоты

```text
GET   /cafes/{cafe_id}/time_slots/
POST  /cafes/{cafe_id}/time_slots/
GET   /cafes/{cafe_id}/time_slots/{slot_id}
PATCH /cafes/{cafe_id}/time_slots/{slot_id}
```

### Бронирования

```text
GET   /booking/
POST  /booking/
GET   /booking/{booking_id}
PATCH /booking/{booking_id}
```

### Медиа

```text
POST /media/
GET  /media/{media_id}
```

### Health-check

```text
GET /health
```

## Переменные окружения

Перед запуском проекта нужно создать файл окружения на основе примера:

```bash
cp infra/.env.example infra/.env
```

Основные переменные окружения:

```env
APP_TITLE=Cafe Booking
APP_DESCRIPTIONS=Cafe Booking.
VERSION=1.0.0
APP_AUTHOR=Author

ALGORITHM=HS256
SECRET=supersecretkey

SUPERUSER_EMAIL=admin@cafebooking.com
SUPERUSER_PASSWORD=userpaswd
SUPERUSER_NAME=superadmin
MIN_PASSWORD_LENGTH=5

DEBUG=False
LOG_LEVEL=DEBUG
LOG_FORMATTER=standard
TIME_FORMAT=%Y-%m-%dT%H:%M:%S
TIME_ZONE=Europe/Moscow

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=cafe
POSTGRES_SERVER=db
POSTGRES_PORT=5432

RABBITMQ_HOST=rabbitmq
RABBITMQ_USER=userrabbit
RABBITMQ_PASS=rabbit
RABBITMQ_VHOST=/
RABBITMQ_PORT=5672

RESULT_BACKEND_URL=rpc://

FLOWER_PORT=5555
FLOWER_BASIC_AUTH=admin:flowerpass

GEVENT_SUPPORT=True

SMTP_SERVER=smtp.mail.ru
SMTP_PORT=465
SMTP_USE_SSL=True
SMTP_USE_TLS=False
SMTP_USER=cafe_booking@mail.ru
SMTP_FROM_EMAIL=cafe_booking@mail.ru
SMTP_PASSWORD=supersecretpasswordforsmtpserver
TIME_FORMAT_MESSAGE=%d.%m.%Y %H:%M
```

Для тестов нужно добавить отдельную базу данных:

```env
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/cafe_test
```

Важно: значение `POSTGRES_SERVER` должно совпадать с именем сервиса PostgreSQL в `docker-compose`. В стандартной конфигурации сервис базы данных называется `db`, поэтому используется:

```env
POSTGRES_SERVER=db
```

## Запуск проекта

### Запуск через Docker Compose

Из директории `infra` выполните:

```bash
cd infra
docker compose up --build
```

Для запуска в фоновом режиме:

```bash
cd infra
docker compose up -d --build
```

После запуска будут доступны:

```text
API:                   http://localhost:8000
Flower:                http://localhost:5555
RabbitMQ Management:   http://localhost:15672
```

Проверить состояние приложения можно через:

```text
http://localhost:8000/health
```

### Локальный запуск внутри DevContainer

Откройте терминал в VSCode внутри DevContainer, перейдите в директорию `src` и выполните:

```bash
cd src
python main.py
```

Проект запустится на порту `8000`.

### Запуск в режиме отладки VSCode

Проект можно запустить через встроенную отладку VSCode:

1. откройте вкладку `Run and Debug`;
2. выберите конфигурацию запуска;
3. нажмите `F5`.

Порт запуска можно изменить в файле:

```text
.vscode/launch.json
```

## Работа через DevContainer

Разработка проекта рассчитана на использование **Dev Containers** в VSCode.

Перед началом работы должны быть установлены:

- Docker;
- VSCode;
- расширение `Dev Containers`.

### Создание DevContainer

Для открытия проекта в контейнере:

1. откройте проект в VSCode;
2. нажмите `Ctrl + Shift + P`;
3. выберите команду `Dev Containers: Reopen in Container`.

После этого начнётся сборка контейнера. В процессе будут установлены Python, uv, зависимости проекта и плагины VSCode.

Если после сборки контейнера VSCode временно подсвечивает установленные пакеты как неизвестные, перезапустите VSCode или дождитесь индексации окружения.

### Настройка Git внутри DevContainer

Так как разработка ведётся внутри контейнера, Git внутри контейнера нужно настроить отдельно.

Укажите имя и email:

```bash
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
```

### Настройка SSH для GitHub внутри DevContainer

Есть два варианта.

Первый вариант — скопировать существующие SSH-ключи с хоста в контейнер:

```text
/home/vscode/.ssh
```

Права доступа должны быть такими:

```text
-rw-------  private_key
-rw-r--r--  public_key.pub
```

Если права неправильные, их можно исправить:

```bash
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

Второй вариант — создать новую пару ключей внутри контейнера и добавить публичный ключ в GitHub:

```text
GitHub -> Settings -> SSH and GPG keys
```

## Миграции

Применение миграций:

```bash
cd src
alembic upgrade head
```

Если используется uv:

```bash
cd src
uv run alembic upgrade head
```

Создание новой миграции:

```bash
cd src
uv run alembic revision --autogenerate -m "migration_name"
```

Откат последней миграции:

```bash
cd src
uv run alembic downgrade -1
```

## Фикстуры

В проекте есть фикстуры для наполнения базы тестовыми данными.

Перед загрузкой фикстур примените миграции:

```bash
cd src
uv run alembic upgrade head
```

Затем задайте `PYTHONPATH`:

```bash
export PYTHONPATH=/workspace/src
```

И запустите загрузку фикстур:

```bash
cd src/fixtures
uv run python gen_load_fixtures.py
```

Если используется загрузчик `load_fixtures.py`, его можно запустить из корня проекта:

```bash
uv run python -m src.fixtures.load_fixtures
```

Фикстуры загружаются в режиме upsert: существующие записи обновляются, новые — добавляются.

## Создание суперпользователя

# При запуске сервиса создается суперпользователь. Учетные данные из .env
- SUPERUSER_EMAIL
- SUPERUSER_PASSWORD
- SUPERUSER_NAME

# Существует возможность создания суперпользователя из консоли

```bash
cd src
PYTHONPATH=$(pwd) uv run scripts/create_superuser.py -l admin@cafe-booking.ru -u Admin -p supersecretpassword
```

## Тесты

Для запуска тестов используется `pytest`.

Тесты используют отдельную базу данных (переменная в .env DB_PYTEST), которая создается автоматически при запуске pytest.

Запуск всех тестов из корня проекта:

```bash
PYTHONPATH=src uv run pytest
```

Запуск с подробным выводом:

```bash
PYTHONPATH=src uv run pytest -vv
```

Запуск тестов конкретной директории:

```bash
PYTHONPATH=src uv run pytest tests/users
```

## Структура проекта

```text
.
├── .devcontainer/
│   ├── devcontainer.json
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── test_tools.sh
├── .vscode/
│   └── launch.json
├── infra/
│   ├── docker-compose.yaml
│   └── .env.example
├── openapi-docs/
│   ├── docs/
│   │   ├── openapi.yml
│   │   ├── openapi.json
│   │   ├── index_swagger.html
│   │   └── index_redoc.html
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   └── readme.md
├── src/
│   ├── api/
│   │   ├── endpoints/
│   │   ├── routers.py
│   │   └── validators.py
│   ├── auth/
│   ├── celery_core/
│   ├── core/
│   │   ├── alembic_models.py
│   │   ├── base_model.py
│   │   ├── db.py
│   │   └── settings.py
│   ├── crud/
│   ├── fixtures/
│   ├── middleware/
│   ├── migrations/
│   ├── models/
│   ├── schemas/
│   ├── celery_app.py
│   └── main.py
├── tests/
│   ├── users/
│   ├── conftest.py
│   ├── constants.py
│   └── helpers.py
├── Dockerfile
├── entrypoint.sh
├── Makefile
├── pyproject.toml
├── ruff.toml
├── uv.lock
└── README.md
```

## Авторизация

Для получения токена нужно отправить запрос:

```http
POST /auth/login
```

Пример тела запроса:

```json
{
  "login": "user@example.com",
  "password": "user_password"
}
```

Пример ответа:

```json
{
  "access_token": "jwt_token",
  "token_type": "bearer"
}
```

Для защищённых эндпоинтов токен нужно передавать в заголовке:

```http
Authorization: Bearer jwt_token
```

## Роли пользователей

В проекте используются три роли:

```text
USER
MANAGER
ADMIN
```

Обычный пользователь может:

- зарегистрироваться;
- авторизоваться;
- получить свой профиль;
- обновить свой профиль.

Менеджер и администратор дополнительно могут:

- получать список пользователей;
- получать пользователя по ID;
- обновлять данные пользователя по ID.

## Работа с медиафайлами

Загрузка изображения:

```http
POST /media/
```

Файл передаётся через `multipart/form-data`.

Поддерживаемые форматы задаются в константах проекта. Загруженное изображение конвертируется и сохраняется в формате JPG.

Получение изображения:

```http
GET /media/{media_id}
```

## Celery, RabbitMQ и Flower

В проекте используется Celery для фоновых задач.

RabbitMQ используется как брокер сообщений.

Flower доступен по адресу:

```text
http://localhost:5555
```

RabbitMQ Management UI доступен по адресу:

```text
http://localhost:15672
```

Данные для базовой авторизации Flower задаются через переменную:

```env
FLOWER_BASIC_AUTH=admin:flowerpass
```

## Линтеры и pre-commit

В проекте используется Ruff для проверки и форматирования кода.

Установка pre-commit hooks:

```bash
uv run pre-commit install
```

Запуск проверки вручную:

```bash
uv run pre-commit run --all-files
```

Запуск Ruff:

```bash
uv run ruff check .
```

Автоисправление Ruff:

```bash
uv run ruff check . --fix
```

## Логи

Логи приложения и Celery сохраняются в Docker volumes:

```text
app_logs
celery_logs
```

Также в проекте есть middleware для логирования HTTP-запросов.

## Примечания для разработки

- Основной код приложения находится в директории `src`.
- OpenAPI-документация проекта находится в `openapi-docs`.
- Тесты находятся в директории `tests`.
- Для тестов обязательно использовать отдельную базу данных.
- Перед запуском приложения нужно заполнить `infra/.env`.
- После изменения моделей нужно создавать и применять миграции Alembic.
- При работе внутри DevContainer Git и SSH-ключи настраиваются отдельно от хостовой системы.
