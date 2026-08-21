"""Equivalent of src/workers/incidentExpiryWorker.js."""
import logging

from celery import shared_task
from django.utils import timezone

from .models import Incident

logger = logging.getLogger(__name__)


@shared_task(name="incidents.tasks.expire_stale_incidents")
def expire_stale_incidents():
    row_count = Incident.objects.filter(
        status="active", expires_at__isnull=False, expires_at__lt=timezone.now()
    ).update(status="expired")

    if row_count > 0:
        logger.info(f"expire_stale_incidents: expired {row_count} stale incidents")
