import ipaddress
import json
import logging
import time
import uuid
from typing import Any

from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from starlette.types import ASGIApp

from core.config import settings

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware логирования."""

    def __init__(
        self,
        app: ASGIApp,
        dispatch: DispatchFunction | None = None,
        log_level: str = 'DEBUG',
    ) -> None:
        """Инициализация middleware логирования."""
        super().__init__(app, dispatch)
        self.log_level = getattr(logging, log_level.upper())

    def _get_userid_username(
        self,
        request: Request,
        user_name: str = 'SYSTEM',
        user_id: str = 'None',
    ) -> tuple[str]:
        """Получить имя пользователя и его id из request.state."""
        user = getattr(request.state, 'user', None)
        return user.username if user else user_name, str(user.id) if user else user_id

    def _is_trusted_proxy(self, ip: str) -> bool:
        """Проверка, доверенный ли прокси."""
        client_ip = ipaddress.ip_address(ip)
        for proxy in settings.get_trusted_proxies:
            if client_ip in ipaddress.ip_network(proxy):
                return True
        return False

    def _get_client_ip(self, request: Request) -> str:
        """Получение IP клиента."""
        forwarded = request.headers.get('x-forwarded-for')
        if forwarded and self._is_trusted_proxy(request.client.host):
            return forwarded.split(',')[0].strip()
        return request.client.host

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Обработка запроса с логированием."""
        trace_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.state.trace_id = trace_id
        client_ip = self._get_client_ip(request)
        user, user_id = self._get_userid_username(request)
        method = request.method
        url_path = request.url.path
        start_time = time.time()
        logger.log(
            self.log_level,
            json.dumps(
                {
                    'user': user,
                    'user_id': user_id,
                    'client_ip': client_ip,
                    'event_type': 'request',
                    'method': method,
                    'path': url_path,
                    'trace_id': trace_id,
                },
                ensure_ascii=False,
            ),
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.log(
                self.log_level,
                json.dumps(
                    {
                        'user': user,
                        'user_id': user_id,
                        'client_ip': client_ip,
                        'event_type': 'response',
                        'method': method,
                        'path': url_path,
                        'trace_id': trace_id,
                        'status_code': response.status_code,
                        'duration_ms': round(process_time * 1000, 2),
                    },
                    ensure_ascii=False,
                ),
            )
            response.headers['X-Request-ID'] = trace_id
            return response

        except Exception as error:
            body = await self._get_request_body(request)
            process_time = time.time() - start_time
            logger.error(
                json.dumps(
                    {
                        'user': user,
                        'user_id': user_id,
                        'client_ip': client_ip,
                        'event_type': 'error',
                        'method': method,
                        'path': url_path,
                        'trace_id': trace_id,
                        'status_code': 500,
                        'duration_ms': round(process_time * 1000, 2),
                        'error': str(error),
                        'body': body,
                    },
                    ensure_ascii=False,
                ),
            )
            raise

    async def _get_request_body(self, request: Request, max_length: int = 1000) -> str:
        """Получение тела запроса."""
        try:
            body_bytes = await request.body()
            if not body_bytes:
                return ''
            body = body_bytes.decode('utf-8')
            if len(body) > max_length:
                body = f'{body[:max_length]} ... truncated, total {len(body)}'  # noqa
            return body
        except Exception as e:  # noqa
            return f'error read body: {e}'
