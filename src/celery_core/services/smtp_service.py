import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from core.config import settings

jinja_env = Environment(
    loader=FileSystemLoader(settings.base_dir_app / 'celery_core/templates'),
    autoescape=select_autoescape(['html', 'xml']),
)


def render_template(template_name: str, **context: dict[str, Any]) -> str:
    """Рендерит Jinja2 шаблона."""
    template = jinja_env.get_template(template_name)
    context.setdefault('year', datetime.now().year)
    return template.render(**context)


def send_email_via_smtp(
    to_email: str | list[str],
    all_recipients: str | list[str],
    subject: str,
    template_name: str,
    context: dict,
) -> dict[str, Any]:
    """Отправка уведомлений на email (поддерживает SSL и TLS).

    Args:
        to_email: Email-адрес(а) для заголовка "To" (видимые получатели).
                 Может быть строкой (один адрес) или списком строк (несколько адресов).
        all_recipients: Полный список получателей для отправки.
                        Может включать адреса, не указанные в to_email (скрытые копии).
                        Формат: строка (один адрес) или список строк (несколько адресов).
        subject: Тема письма.
        template_name: Имя Jinja2-шаблона (путь относительно директории templates).
        context: Словарь с данными для рендеринга шаблона.

    """
    msg = MIMEMultipart()
    msg['From'] = settings.smtp_from_email
    msg['To'] = ', '.join(to_email)
    msg['Subject'] = subject

    html_body = render_template(template_name, **context)
    msg.attach(MIMEText(html_body, 'html'))

    failed_recipients = {}
    if settings.smtp_use_ssl:
        failed_recipients = _send_email_via_ssl(all_recipients, msg)
    elif settings.smtp_use_tls:
        failed_recipients = _send_email_via_tls(all_recipients, msg)
    else:
        raise ValueError(
            'Не указан протокол шифрования (smtp_use_ssl, smtp_use_tls) для SMTP сервера.',
        )

    return {
        'status': 'sent',
        'to': all_recipients,
        'failed_recipients': failed_recipients,
        'sent_at': datetime.now().isoformat(),
    }


def _send_email_via_ssl(to_recipients: list[str], msg: Any) -> dict[Any, Any]:
    """Отправка через SSL."""
    with smtplib.SMTP_SSL(
        settings.smtp_server,
        settings.smtp_port,
        context=ssl.create_default_context(),
    ) as server:
        server.login(settings.smtp_user, settings.smtp_password)

        return server.sendmail(
            from_addr=settings.smtp_from_email,
            to_addrs=to_recipients,
            msg=msg.as_string(),
        )


def _send_email_via_tls(to_recipients: list[str], msg: Any) -> dict[Any, Any]:
    """Отправка через STARTTLS."""
    with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)

        return server.sendmail(
            from_addr=settings.smtp_from_email,
            to_addrs=to_recipients,
            msg=msg.as_string(),
        )
