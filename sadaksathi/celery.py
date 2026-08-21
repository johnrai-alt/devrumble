"""
Equivalent of src/workers/*.js. Each worker used node-cron to schedule an
async function on an interval; here the same functions become Celery tasks
(defined in each app's tasks.py) and the schedule moves into CELERY_BEAT_SCHEDULE.

Run with:
    celery -A sadaksathi worker -l info
    celery -A sadaksathi beat -l info
(or `celery -A sadaksathi worker -B -l info` to run both in one process,
 handy for local dev — same spirit as server.js starting all three workers
 in-process.)
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sadaksathi.settings")

app = Celery("sadaksathi")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # ingestWorker.js: cron.schedule('*/2 * * * *', pollTrafficProvider)
    "poll-traffic-provider": {
        "task": "traffic.tasks.poll_traffic_provider",
        "schedule": crontab(minute="*/2"),
    },
    # incidentExpiryWorker.js: cron.schedule('*/5 * * * *', expireStaleIncidents)
    "expire-stale-incidents": {
        "task": "incidents.tasks.expire_stale_incidents",
        "schedule": crontab(minute="*/5"),
    },
    # aggregationWorker.js: cron.schedule('5 * * * *', aggregatePastHour)
    "aggregate-past-hour": {
        "task": "analytics.tasks.aggregate_past_hour",
        "schedule": crontab(minute=5),
    },
}
