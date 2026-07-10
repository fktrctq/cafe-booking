from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import PydanticBaseSettingsSource

BASE_DIR_PROJECT = Path(__file__).resolve().parent.parent.parent
ENV_DEV = BASE_DIR_PROJECT / 'infra' / '.env'


class Settings(BaseSettings):
    """Настройки приложения."""

    # Base settings app
    version: str = '2.1.0'
    app_title: str = 'App title'
    app_descriptions: str = 'App name'
    app_author: str = 'Author Name'
    secret: str = 'supersecretkey'
    base_dir_app: Path = Path(__file__).resolve().parent.parent
    superuser_email: Optional[str] = None
    superuser_name: Optional[str] = None
    superuser_password: Optional[str] = None
    min_password_length: int = 5
    log_to_file: bool = False
    log_level: str = 'DEBUG'
    log_formatter: str = 'json'
    log_dir: str = 'logs'
    time_format: str = '%Y-%m-%dT%H:%M:%S'
    time_zone: Optional[str] = 'Europe/Moscow'
    allow_origins: str = 'http://localhost:8000,http://127.0.0.1:8000'
    trusted_proxy: Optional[str] = '172.16.0.0/24,127.0.0.1'
    # Token
    algorithm: str = 'HS256'
    token_type: str = 'bearer'
    token_life_hours: int = 1
    token_format: str = 'jwt'
    # PostgreSQL
    postgres_user: str = 'postgres'
    postgres_password: str = 'postgres'
    postgres_db: str = 'cafe'
    db_pytest: str = 'cafe_test'
    postgres_host: str = 'db'
    postgres_port: str = '5432'
    # Database connect settings
    backend_db_pool_size: int = 100
    backend_db_max_overflow: int = 150
    backend_db_pool_timeout: int = 30
    backend_db_pool_recycle: int = 3600
    celery_db_pool_size: int = 50
    celery_db_max_overflow: int = 100
    celery_db_pool_timeout: int = 60
    celery_db_pool_recycle: int = 1800
    # Broker messages
    rabbitmq_host: str = 'rabbitmq'
    rabbitmq_default_user: str = 'userrabbit'
    rabbitmq_default_pass: str = 'rabbit'
    rabbitmq_default_vhost: str = '/'
    rabbitmq_port: str = '5672'
    result_backend_url: Optional[str] = 'rpc://'
    # Configuring email sending (SMTP)
    smtp_server: str = 'smtp.mail.ru'
    smtp_port: int = 465
    smtp_use_ssl: bool = True
    smtp_use_tls: bool = False
    smtp_user: str = 'cafe@booking.ru'
    smtp_password: str = 'superpassword'
    smtp_from_email: str = 'cafe@booking.ru'
    time_format_message: str = '%d.%m.%Y %H:%M'
    # Celery
    worker_concurrency: int = 10
    max_retries: int = 3
    rate_limit: str = '100/m'
    # Media files
    max_file_size: int = 5242880
    allowed_extensions_media: str = '.jpg,.jpeg,.png'
    # Redis cache
    redis_host: str = 'redis'
    redis_port: int = 6379
    redis_max_connections: int = 200
    redis_max_reconnect_backoff: int = 120

    model_config = SettingsConfigDict(
        env_file=(ENV_DEV if ENV_DEV.exists() else '.env'),
        env_file_encoding='utf-8',
        extra='ignore',
    )

    @property
    def max_file_size_mb(self) -> int:
        """Размер медиа файла в МБ."""
        return round(self.max_file_size / (1024 * 1024))

    @property
    def allowed_extensions(self) -> list[str]:
        """Список допустимых разрешений для медиа-файлов."""
        return self.allowed_extensions_media.split(',')

    @property
    def base_dir_media(self) -> Path:
        """Директория для хранения медиа-файлов."""
        return self.base_dir_app / 'media'

    @property
    def get_allow_origins(self) -> list[str]:
        """Список CROS доменов."""
        return self.allow_origins.split(',')

    @property
    def get_trusted_proxies(self) -> list[str]:
        """Получить список доверенных прокси серверов."""
        return self.trusted_proxy.split(',')

    @property
    def get_time_zone(self) -> ZoneInfo:
        """Объект часового пояса."""
        return ZoneInfo(self.time_zone)

    @property
    def broker_url(self) -> str:
        """Строка подключения к брокеру сообщений."""
        return (
            f'amqp://{self.rabbitmq_default_user}:'
            f'{self.rabbitmq_default_pass}@{self.rabbitmq_host}:'
            f'{self.rabbitmq_port}/{self.rabbitmq_default_vhost}'
        )

    @property
    def database_async_url(self) -> str:
        """Строка асинхронного подключения к БД."""
        return (
            f'postgresql+asyncpg://{self.postgres_user}:'
            f'{self.postgres_password}@{self.postgres_host}:'
            f'{self.postgres_port}/{self.postgres_db}'
        )

    @property
    def database_sync_url(self) -> str:
        """Строка синхронного подключения к БД."""
        return (
            f'postgresql+psycopg2://{self.postgres_user}:'
            f'{self.postgres_password}@{self.postgres_host}:'
            f'{self.postgres_port}/{self.postgres_db}'
        )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Переопределяем приоритеты источников переменных для dev и prom."""
        if ENV_DEV.exists():
            return (init_settings, dotenv_settings, env_settings, file_secret_settings)
        return (init_settings, file_secret_settings, env_settings, dotenv_settings)


settings = Settings()
