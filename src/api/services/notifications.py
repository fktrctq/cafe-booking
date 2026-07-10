import logging

from celery_core.tasks import send_notification
from models import Booking, BookingStatus

logger = logging.getLogger(__name__)


def notify_booking_status(booking: Booking, is_new: bool = False) -> None:
    """Формирование задачи отправки уведомлений о статусе бронирования."""
    try:
        match booking.status:
            case BookingStatus.BOOKING:
                if is_new:
                    task = send_notification.delay(booking_id=booking.id, notify_type='booking')
                    logger.info(
                        f'Создание бронирования, ID {booking.id}: задача ID {task.id} отправлена в очередь',
                    )
                else:
                    task = send_notification.delay(booking_id=booking.id, notify_type='modified')
                    logger.info(
                        f'Изменение бронирования, ID {booking.id}: задача ID {task.id} отправлена в очередь',
                    )

            case BookingStatus.ACTIVE | BookingStatus.COMPLETED:
                logger.info(
                    f'Бронирование ID {booking.id}: статус {booking.status.value}, уведомление не требуется',
                )

            case BookingStatus.CANCELED:
                task = send_notification.delay(booking_id=booking.id, notify_type='canceled')
                logger.info(f'Отмена бронирования, ID {booking.id}: задача ID {task.id} отправлена в очередь')

            case _:
                logger.error(f'Неизвестный статус бронирования, ID {booking.id}: {booking.status}')

    except Exception as e:
        logger.error(f'Ошибка при отправке уведомления для бронирования {booking.id}: {e}')
