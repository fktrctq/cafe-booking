import logging.config
from typing import Any

from celery import Celery
from celery.signals import setup_logging

from core.logging_conf import LOGGING

logging.config.dictConfig(LOGGING)

app = Celery('celery_app')
app.config_from_object('celery_core.config')


@setup_logging.connect
def configure_logging(**kwargs: Any) -> None:
    """Применение конф-ии логера для воркеров."""
    logging.config.dictConfig(LOGGING)


# Автоматическое обнаружение задач
app.autodiscover_tasks(['celery_core.tasks'])
