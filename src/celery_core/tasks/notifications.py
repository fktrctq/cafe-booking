import logging
from datetime import datetime
from smtplib import SMTPException
from typing import Any

from celery_app import app
from celery_core.base import BaseTask
from celery_core.services.booking_service import get_booking_with_relations, get_upcoming_bookings
from celery_core.services.notification_service import (
    build_notify_context,
    get_emails_recipients,
)
from celery_core.services.smtp_service import send_email_via_smtp

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    base=BaseTask,
    name='tasks.send_upcoming_bookings',
)
def send_upcoming_bookings(
    self: BaseTask,
    reminder_minutes_before: int = 60,
    task_interval_minutes: int = 10,
    notify_target: str = 'both',
) -> dict:
    """Проверяет бронирования и отправляет напоминания.

    Args:
        self: экземпляр задачи Celery.
        reminder_minutes_before: За сколько минут до начала бронирования отправлять напоминание.
        task_interval_minutes: Интервал выполнения задачи в минутах (для расчета окна).
        notify_target: Кого оповещать: 'client', 'manager', 'both'.

    """
    try:
        upcoming_bookings = get_upcoming_bookings(
            reminder_minutes_before,
            task_interval_minutes,
            self.get_session(),
        )
    except Exception as e:
        logger.error(f'Ошибка получения списка объектов бронирования: {e}')
        return {
            'error': str(e),
            'reminder_minutes_before': reminder_minutes_before,
            'task_interval_minutes': task_interval_minutes,
        }

    if not upcoming_bookings:
        return {'status': 'completed', 'bookings_found': 0}

    logger.debug(f'Found {len(upcoming_bookings)} upcoming bookings')

    for booking_id in upcoming_bookings:
        send_notification.delay(booking_id, 'reminder', notify_target)

    return {
        'status': 'completed',
        'checked_at': datetime.now().isoformat(),
        'bookings_found': len(upcoming_bookings),
        'reminder_minutes_before': reminder_minutes_before,
        'notify_target': notify_target,
    }


@app.task(
    bind=True,
    base=BaseTask,
    name='tasks.send_notification',
    autoretry_for=(SMTPException, ConnectionError, TimeoutError),
)
def send_notification(
    self: BaseTask,
    booking_id: Any,
    notify_type: str = 'booking',
    notify_target: str = 'both',
) -> dict:
    """Отправка уведомления.

    Args:
        self: экземпляр задачи Celery
        booking_id: id бронирования
        notify_type:
                        - booking - создание бронирования
                        - canceled - отмена бронирования
                        - modified - изменение бронирования
                        - reminder - напоминание о бронировании
        notify_target: Кого оповещать: 'client', 'manager', 'both'.

    """
    try:
        booking = get_booking_with_relations(booking_id, self.get_session())
        if not booking:
            error = f'Booking {booking_id} not found'
            logger.warning(error)
            return {'error': error}
    except Exception as e:
        logger.error(f'Ошибка получения объекта бронирования: {e}')
        return {'error': str(e), 'booking_id': booking_id}

    try:
        to_recipient, all_recipients = get_emails_recipients(booking, notify_target)
    except Exception as e:
        logger.error(f'Ошибка подготовки списка получателей уведомления: {e}')
        return {'error': str(e), 'booking_id': booking_id}

    try:
        context = build_notify_context(booking, notify_type)
    except Exception as e:
        logger.error(f'Ошибка подготовки контекста уведомления: {e}')
        return {'error': str(e), 'booking_id': booking_id}

    try:
        result = send_email_via_smtp(
            to_email=to_recipient,
            all_recipients=all_recipients,
            subject=context.get('title', 'Уведомление'),
            template_name='booking_notification.html',
            context=context,
        )
    except Exception as e:
        logger.error(f'Ошибка отправки уведомления: {e}')
        return {'error': str(e), 'booking_id': booking_id}

    logger.info(
        f'Reminder sent for booking {booking_id} to {len(all_recipients)} recipients: {all_recipients}',
    )

    return {
        'booking_id': booking_id,
        'to_email': all_recipients,
        'status': result,
    }
