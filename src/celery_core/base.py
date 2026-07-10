import logging
from contextlib import contextmanager
from typing import Any, Generator

from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings
from core.constants import INTERNAL_DB_ERROR

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_sync_url,
    pool_size=settings.celery_db_pool_size,
    max_overflow=settings.celery_db_max_overflow,
    pool_timeout=settings.celery_db_pool_timeout,
    pool_pre_ping=True,
    pool_recycle=settings.celery_db_pool_recycle,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DatabaseTask(Task):
    """Базовый класс задач с подключением БД."""

    def get_session(self) -> Session:
        """Создаёт новую сессию."""
        return SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Контекстный менеджер с автоматическим управлением транзакцией."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as error:
            session.rollback()
            logger.error(f'{INTERNAL_DB_ERROR}: {error}')
            raise
        except Exception as error:
            session.rollback()
            logger.critical(f'{INTERNAL_DB_ERROR}: {error}')
            raise
        finally:
            session.close()


class LoggedTask(Task):
    """Базовый класс задач с логированием."""

    def before_start(self, task_id: Any, args: Any, kwargs: Any) -> None:
        """Метод, вызываемый перед выполнением задачи."""
        logging.debug(f'Task {self.name} id {task_id} starting with args {args}')
        super().before_start(task_id, args, kwargs)

    def on_failure(self, exc: Any, task_id: Any, args: Any, kwargs: Any, einfo: Any) -> None:
        """Метод, вызываемый при ошибке выполнения задачи."""
        logger.error(f'Task {self.name} id {task_id} failed: {exc}', exc_info=True)
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval: Any, task_id: Any, args: Any, kwargs: Any) -> None:
        """Метод, вызываемый при успешном выполнении задачи."""
        logger.debug(f'Task {self.name} id {task_id} succeeded: {task_id}')
        super().on_success(retval, task_id, args, kwargs)

    def after_return(
        self,
        status: Any,
        retval: Any,
        task_id: Any,
        args: Any,
        kwargs: Any,
        einfo: Any,
    ) -> None:
        """Метод, вызываемый после возврата из задачи."""
        logger.debug(f'Task {self.name} id {task_id} finished with status: {status}')
        super().after_return(status, retval, task_id, args, kwargs, einfo)


class BaseTask(DatabaseTask, LoggedTask):
    """Объединенный базовый класс с логированием и подключением к БД.

    Наследует:
    - DatabaseTask: методы для работы с БД (get_session, session_scope)
    - LoggedTask: методы для логирования (before_start, on_failure, on_success, after_return)
    """

    abstract = True
