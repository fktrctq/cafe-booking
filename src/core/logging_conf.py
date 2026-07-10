import json
import logging
import os
from typing import Any

from core.config import settings

LOG_DIR = os.path.join(settings.base_dir_app, settings.log_dir)
os.makedirs(LOG_DIR, exist_ok=True)
handlers = ['console', 'file'] if settings.log_to_file else ['console']


class JSONFormatter(logging.Formatter):
    """JSON форматтер для структурированных логов (Kibana/ELK)."""

    def format(self, record: Any) -> str:
        """Форматирует запись лога в JSON строку."""
        log_dict = {
            'time': self.formatTime(record, settings.time_format),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'line': record.lineno,
        }

        if isinstance(record.msg, dict):
            log_dict.update(record.msg)
        else:
            log_dict['message'] = record.getMessage()

        if record.exc_info:
            log_dict['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_dict, ensure_ascii=False)


class StandardFormatter(logging.Formatter):
    """Человекочитаемый форматтер."""

    # ANSI-коды цветов
    COLOR_CODES = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[1;31m',
    }
    RESET_CODE = '\033[0m'

    def format(self, record: Any) -> str:
        """Форматирует запись лога в читаемый текстовый формат."""
        time = self.formatTime(record, settings.time_format)
        level = record.levelname
        logger = record.name

        color = self.COLOR_CODES.get(level, '')
        colored_level = f'{color}{level}{self.RESET_CODE}'

        if isinstance(record.msg, dict):
            msg = json.dumps(record.msg, ensure_ascii=False)
        else:
            msg = record.getMessage()

        if record.levelno >= logging.ERROR:
            return f'[{time}] [{colored_level}] [{logger}] [{record.module}:{record.lineno}] {msg}'

        return f'[{time}] [{colored_level}] [{logger}] {msg}'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {'()': StandardFormatter},
        'json': {'()': JSONFormatter},
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': settings.log_formatter,
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'app.log'),
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'encoding': 'utf-8',
            'formatter': settings.log_formatter,
        },
    },
    'loggers': {
        '': {
            'handlers': handlers,
            'level': settings.log_level,
        },
        'uvicorn': {
            'handlers': handlers,
            'level': settings.log_level,
            'propagate': False,
        },
        'uvicorn.access': {
            'handlers': handlers,
            'level': settings.log_level,
            'propagate': False,
        },
        'uvicorn.error': {
            'handlers': handlers,
            'level': settings.log_level,
            'propagate': False,
        },
    },
}
