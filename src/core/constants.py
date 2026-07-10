"""Константы и магические числа, используемые в проекте."""

from core.config import settings

# Константы медиа-файлы

# Сообщение об ошибке формата медиа-файла
ACCEPTABLE_FORMATS = f'Допустимые форматы: {", ".join(settings.allowed_extensions)}'
# Сообщение об ошибке создания файла
FILE_NOT_FOUND = 'Файл не найден на диске.'
# Сообщение об ошибке размера медиа-файла
MAX_FILE_SIZE_ERROR = f'Размер файла не должен превышать {settings.max_file_size_mb} МБ.'
# Сообщение об ошибке чтения медиа-файла
READ_IMAGE_ERROR = 'Не удалось прочитать изображение.'
# Размер сегмента
UPLOAD_CHUNK_SIZE = 1048576

# Константы моделей/cхем

# Максимальная длина имени директории файла
MAX_MEDIA_PATH_LENGTH = 255
# Максимальная длина описания
MAX_DESCRIPTION_LENGTH = 500
# Максимальная длина комментария к бронированию
MAX_NOTE_LENGTH = 800
# Максимальное название кафе
MAX_NAME_LENGTH = 120
# Максимальная длина адреса
MAX_ADDRESS_LENGTH = MAX_NAME_LENGTH
# Максимальная длина номера телефона
PHONE_LENGTH = 12
# Максимальная длина имени пользователя
MAX_USERNAME_LENGTH = 80
# Максимальная длина поля e-mail
MAX_EMAIL_LENGTH = 120
# Максимальная длина хешированного пароля
MAX_HASHED_PASSWORD_LENGTH = 256
# Минимальная длина пароля
MIN_PASSWORD_LENGTH = settings.min_password_length
# Минимальная длина имени пользователя
MIN_USERNAME_LENGTH = 3
# Минимальная длина любой строки
MIN_ANYSTR_LENGTH = 1
# Паттерн номера телефона
PHONE_PATTERN = r'^(\+?[78])?[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{2})[-.\s]?(\d{2})$'
# Паттерн имени пользователя
NAME_PATTERN = r'^[a-zA-Z0-9_-]+$'
# Регулярные выражения
EMAIL_REGEX = r'^[^@]+@[^@]+\.[^@]+$'

# Константы для процесса ауентификации
TOKEN_TYPE = settings.token_type
TOKEN_LIFE_HOURS = settings.token_life_hours
TOKEN_FORMAT = settings.token_format

# Константы телефона
NORMALIZED_PHONE_LENGTH = 10
PHONE_PREFIX_LENGTH = 11
RU_PHONE_PREFIXES = ('7', '8')

# Ошибки пользователей
ONLY_ADMIN_CAN_CHANGE_ROLE = 'Только администратор может менять роль пользователя.'
ONLY_ADMIN_CAN_CHANGE_STATUS = 'Только администратор может менять статус активности пользователя.'
ADMIN_CANT_CHANGE_OWN_ROLE = 'Нельзя поменять свою роль.'
ADMIN_CANT_CHANGE_OWN_STATUS = 'Нельзя поменять свой статус активности.'
ACCESS_DENIED_ERROR = 'Доступ запрещен.'
USER_CONTACT_REQUIRED_ERROR = 'Email или номер телефона обязательны для заполнения.'
USER_NOT_FOUND_ERROR = 'Пользователь не найден.'
INVALID_EMAIL = 'Не правильный формат почтового адреса.'
INVALID_PHONE = 'Не правильный формат номера телефона'
USER_UPDATE_RULES = {
    'role': {
        'no_permission_error': ONLY_ADMIN_CAN_CHANGE_ROLE,
        'self_action_error': ADMIN_CANT_CHANGE_OWN_ROLE,
    },
    'is_active': {
        'no_permission_error': ONLY_ADMIN_CAN_CHANGE_STATUS,
        'self_action_error': ADMIN_CANT_CHANGE_OWN_STATUS,
    },
}
UNIQUE_USER_FIELDS = (
    'username',
    'email',
    'phone',
    'tg_id',
)
UNIQUE_USER_FIELD_ERRORS = {
    'username': 'Имя пользователя уже занято.',
    'email': 'Адрес электронной почты уже зарегистрирован.',
    'phone': 'Номер телефона уже зарегистрирован.',
    'tg_id': 'Telegram id уже зарегистрирован.',
}

# Ошибки auth
NOT_AUTHENTICATED_ERROR = 'Необходимо выполнить вход в систему.'
INVALID_TOKEN_ERROR = 'Невалидный токен.'
EXPIRED_TOKEN_ERROR = 'Попытка авторизации с просроченным токеном.'
JWT_USER_ID_NOT_FOUND_ERROR = 'User_id не был найден в JWT Payload.'
INVALID_CREDENTIALS_ERROR = 'Неверный логин или пароль.'

# Ошибки валидации
OBJECT_NOT_FOUND_ERROR = 'Запрашиваемый объект не найден.'
OBJECT_NOT_BELONG_TO_CAFE_ERROR = 'Запрашиваемый объект не принадлежит указанному кафе.'
CAFE_UNIQUE_CONSTRAINT_ERROR = 'Кафе с таким названием, адресом и номером телефона уже существует!'
CAFE_STATUS_CHANGE_ERROR = 'Только администратор может менять статус активности кафе.'
SLOT_ALREADY_EXISTS_ERROR = 'Слот с таким временем уже существует в этом кафе.'
BOOKING_ACTIVE_UPDATE_ERROR = 'Нельзя изменить активное бронирование.'
BOOKING_PAST_UPDATE_ERROR = 'Нельзя изменить прошедшее бронирование.'
BOOKING_PAST_CREATE_ERROR = 'Нельзя забронировать столик на прошедшую дату.'
BOOKING_SLOT_BUSY_ERROR = 'Выбранный столик в указанный временной слот уже забронирован.'
BOOKING_USER_OVERLAP_ERROR = 'Бронирования пользователя не должны пересекаться по времени.'

# Ошибки сервиса
INTERNAL_DB_ERROR = 'Ошибка при получении данных. Пожалуйста, попробуйте позже.'
INTERNAL_SERVER_ERROR = 'Непредвиденная ошибка работы сервиса'

# JWT
JWT_SUB_FIELD = 'sub'
