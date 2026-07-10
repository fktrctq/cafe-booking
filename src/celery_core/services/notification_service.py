from models import Booking

notification_data = {
    'booking': {
        'title': 'Создание бронирования',
        'message': 'Бронирование успешно создано.',
        'status_text': 'Создано',
    },
    'canceled': {
        'title': 'Отмена бронирования',
        'message': 'Бронирование отменено.',
        'status_text': 'Отменено',
    },
    'modified': {
        'title': 'Изменение бронирования',
        'message': 'Детали бронирования изменены.',
        'status_text': 'Изменено',
    },
    'reminder': {
        'title': 'Напоминание о бронировании',
        'message': 'Напоминаем о предстоящем бронировании.',
        'status_text': 'Напоминание',
    },
}


def get_emails_recipients(booking: Booking, notify_target: str) -> tuple[list, list]:
    """Подготовить списки получателей уведомления.

    Args:
        booking: Объект бронирования, содержащий информацию о клиенте и кафе.
        notify_target: Цель оповещения: 'client', 'manager' или 'both'.

    Returns:
        to_recipients: получатели, которые будут видны в поле "Кому" (To).
        all_recipients: полный список получателей для отправки (включая скрытых).

    """
    all_recipients = []
    if notify_target == 'both':
        all_recipients = [manager.email for manager in booking.cafe.managers if manager.email]
        to_recipients = [booking.user.email] if booking.user and booking.user.email else []
    elif notify_target == 'manager':
        to_recipients = [manager.email for manager in booking.cafe.managers if manager.email]
    else:
        to_recipients = [booking.user.email] if booking.user and booking.user.email else []
    all_recipients.extend(to_recipients)

    return to_recipients, all_recipients


def build_notify_context(booking: Booking, notify_type: str) -> dict:
    """Создание контекста для Jinja2 шаблона."""
    data = notification_data.get(notify_type)

    seat_numbers = [str(ts.table.seat_number) for ts in booking.tables_slots]
    slot_time_start = booking.tables_slots[0].slot.start_time.strftime('%H:%M')

    return {
        'title': data.get('title', ''),
        'message': data.get('message', ''),
        'status_text': data.get('status_text', ''),
        'user_name': booking.user.username,
        'cafe_name': booking.cafe.name,
        'slot_time_start': slot_time_start,
        'seat_numbers': ', '.join(seat_numbers),
        'booking_date': booking.booking_date,
        'status_class': notify_type,
        'menu_items': None,
    }
