import pytest

from tests.constants import (
    ADMIN_EMAIL,
    ADMIN_INDEX,
    ADMIN_ROLE,
    ADMIN_USER_NAME,
    MANAGER_EMAIL,
    MANAGER_INDEX,
    MANAGER_ROLE,
    MANAGER_USER_NAME,
)
from tests.helpers import make_unique_user_payload, make_user_payload


@pytest.fixture
def user_payload() -> dict:
    """Валидный payload обычного пользователя."""
    return make_user_payload()


@pytest.fixture
def another_user_payload() -> dict:
    """Валидный payload второго пользователя."""
    return make_unique_user_payload(index=2)


@pytest.fixture
def admin_payload() -> dict:
    """Payload администратора.

    Сейчас auth/permissions ещё не реализованы, но фикстура пригодится позже.
    """
    return make_unique_user_payload(
        index=ADMIN_INDEX,
        username=ADMIN_USER_NAME,
        email=ADMIN_EMAIL,
        role=ADMIN_ROLE,
    )


@pytest.fixture
def manager_payload() -> dict:
    """Payload менеджера.

    Сейчас auth/permissions ещё не реализованы, но фикстура пригодится позже.
    """
    return make_unique_user_payload(
        index=MANAGER_INDEX,
        username=MANAGER_USER_NAME,
        email=MANAGER_EMAIL,
        role=MANAGER_ROLE,
    )
