from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "gitauto_workers",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_always_eager=settings.celery_task_always_eager,
    result_expires=86400,
)

