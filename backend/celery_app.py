from celery import Celery

# Define your Redis URL (adjust host/port if using Docker)
REDIS_URL = "redis://localhost:6379/0"

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Automatically look for tasks inside a tasks.py file
celery_app.autodiscover_tasks(["tasks"])

# Optional configuration tweaks
celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,  # Expire task results in 1 hour
)
