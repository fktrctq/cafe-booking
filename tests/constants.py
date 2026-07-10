from http import HTTPStatus

USERS_URL = '/api/v1/users/'
USER_DETAIL_URL = '/api/v1/users/{user_id}'

VALID_USER_PASSWORD = 'strong_password'
UPDATED_USER_PASSWORD = 'new_strong_password'

DEFAULT_USER_ROLE = 'USER'

USER_NAME = 'test_user'
EMAIL = 'test_user@example.com'
PHONE = '9123456789'
NORMALIZED_PHONE = '9123456789'
TG_ID = '123456789'

ADMIN_INDEX = 10
ADMIN_USER_NAME = 'admin_user'
ADMIN_EMAIL = 'admin@example.com'
ADMIN_ROLE = 'ADMIN'

MANAGER_INDEX = 20
MANAGER_USER_NAME = 'manager_user'
MANAGER_EMAIL = 'manager@example.com'
MANAGER_ROLE = 'MANAGER'

UPDATED_USERNAME = 'updated_user'
UPDATED_EMAIL = 'updated_user@example.com'
UPDATED_PHONE = '9234567890'
UPDATED_NORMALIZED_PHONE = '9234567890'
UPDATED_TG_ID = '987654321'

DUPLICATE_USERNAME_ERROR = 'Имя пользователя уже занято.'
DUPLICATE_EMAIL_ERROR = 'Адрес электронной почты уже зарегистрирован.'

AUTH_LOGIN_URL = '/api/v1/auth/login'
USERS_ME_URL = '/api/v1/users/me'

AUTH_TOKEN_FIELD = 'access_token'
TOKEN_TYPE_FIELD = 'token_type'
AUTH_HEADER_NAME = 'Authorization'
BEARER_TOKEN_PREFIX = 'Bearer'

INVALID_LOGIN = 'wrong_user@example.com'
INVALID_PASSWORD = 'wrong_password'
MALFORMED_TOKEN = 'not.a.valid.jwt'

NOT_FOUND_STATUS = HTTPStatus.NOT_FOUND
OK_STATUS = HTTPStatus.OK
CREATED_STATUS = HTTPStatus.CREATED
BAD_REQUEST_STATUS = HTTPStatus.BAD_REQUEST
VALIDATION_ERROR_STATUS = HTTPStatus.UNPROCESSABLE_ENTITY
UNAUTHORIZED_STATUS = HTTPStatus.UNAUTHORIZED
FORBIDDEN_STATUS = HTTPStatus.FORBIDDEN

INVALID_UUID = 'not-a-valid-uuid'
UNKNOWN_UUID = '00000000-0000-0000-0000-000000000000'

PASSWORD_FIELD = 'password'

PUBLIC_USER_FIELDS = {
    'id',
    'username',
    'email',
    'phone',
    'tg_id',
    'role',
    'is_active',
    'created_at',
    'updated_at',
}
