"""Celery application configuration — Phase 4 production async execution layer.

Replaces FastAPI BackgroundTasks with Redis-backed Celery workers.
"""

import os
from celery import Celery
from src.core.telemetry import init_tracing, instrument_celery, instrument_redis

# Initialize tracing for Celery worker process
tracer = init_tracing()
instrument_celery()
instrument_redis()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ecodream",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "src.services.celery_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,
    result_expires=3600,  # 1 hour
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "heartbeat-every-60s": {
        "task": "src.services.celery_tasks.heartbeat",
        "schedule": 60.0,
    },
    "check-cron-jobs-every-minute": {
        "task": "src.services.celery_tasks.check_and_execute_cron_jobs",
        "schedule": 60.0,
    },
}
