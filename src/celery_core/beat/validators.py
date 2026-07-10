from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.orm import Session

from celery_core.beat.crud import periodic_task_crud


def check_task_exists_by_name(name: str, session: Session) -> None:
    """Проверить, что задача с таким именем не существует."""
    if periodic_task_crud.get_by_attributes(session, name=name):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f'Задача с именем {name} уже существует',
        )
