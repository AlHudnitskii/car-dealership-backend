import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("car_dealership")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "dealership-purchase-from-suppliers": {
        "task": "apps.dealerships.tasks.process_dealership_purchases",
        "schedule": crontab(minute="*/10"),
        "options": {
            "expires": 540,
        },
    },
    "update-preferred-suppliers": {
        "task": "apps.dealerships.tasks.update_all_preferred_suppliers",
        "schedule": crontab(minute=0),
        "options": {
            "expires": 3000,
        },
    },
    "process-customer-offers": {
        "task": "apps.transactions.tasks.process_pending_offers",
        "schedule": crontab(minute="*/5"),
        "options": {
            "expires": 240,
        },
    },
    "cleanup-expired-offers": {
        "task": "apps.transactions.tasks.cleanup_expired_offers",
        "schedule": crontab(hour=3, minute=0),
    },
    "generate-daily-reports": {
        "task": "apps.stats.tasks.generate_daily_reports",
        "schedule": crontab(hour=23, minute=50),
    },
}

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=270,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
