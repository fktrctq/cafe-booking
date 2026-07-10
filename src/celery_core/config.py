from sqlalchemy_celery_beat.schedulers import DatabaseScheduler

from core.config import settings

broker_url = settings.broker_url
result_backend = settings.result_backend_url
accept_content = ['json']
result_serializer = 'json'
result_persistent = False  # Не сохранять результаты на диск
result_expires = 3600  # Автоматически удалять результаты через час
timezone = settings.time_zone
enable_utc = True
# Настройки задач
task_serializer = 'json'
task_track_started = True  # Отслеживать начало выполнения
task_time_limit = 30 * 60  # 30 минут максимум
task_soft_time_limit = 25 * 60  # 25 минут мягкий лимит
task_acks_late = True  # Подтверждать только после выполнения
task_reject_on_worker_lost = True  # Отклонить задачу при потере воркера
task_default_queue = 'default'
task_default_exchange = 'default'
task_default_routing_key = 'default'
# Ограничения на задачи (rate limits)
task_annotations = {
    '*': {
        'max_retries': settings.max_retries,  # кол-во повторений при ошибке
        'retry_backoff': True,  # Включает экспоненциальную задержку
        'retry_backoff_max': 600,  # Максимальная задержка (10 минут)
        'retry_jitter': True,  # Добавляет случайный разброс, чтобы избежать "эффекта стада"
    },
    'celery_core.tasks.send_notification': {
        'rate_limit': settings.rate_limit,
    },
}
# Настройки воркера
worker_prefetch_multiplier = 2
worker_max_tasks_per_child = 500  # Перезапускать воркер после N задач (защита от утечек)
worker_concurrency = settings.worker_concurrency
worker_disable_rate_limits = False  # Включить rate limits
worker_hijack_root_logger = False  # Отключаем переопределение дефолтного логера
worker_send_task_events = True  # Все события задач отправляются в мониторинг (Flower, Metrics)
worker_log_level = settings.log_level
# sqlalchemy_celery_beat
beat_dburi = settings.database_sync_url
beat_scheduler = DatabaseScheduler
# beat_schema = None
