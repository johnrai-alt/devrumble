"""Equivalent of src/workers/aggregationWorker.js."""
import logging

from celery import shared_task
from django.db import connection

logger = logging.getLogger(__name__)


@shared_task(name="analytics.tasks.aggregate_past_hour")
def aggregate_past_hour():
    """
    Rolls up raw traffic_readings from the last completed hour into
    congestion_hourly_agg, so the analytics module never reads live tables.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO congestion_hourly_agg (segment_id, hour_bucket, avg_speed_kph, avg_congestion_level)
            SELECT
              segment_id,
              date_trunc('hour', recorded_at) AS hour_bucket,
              avg(speed_kph),
              avg(congestion_level)
            FROM traffic_readings
            WHERE recorded_at >= date_trunc('hour', now() - interval '1 hour')
              AND recorded_at < date_trunc('hour', now())
            GROUP BY segment_id, date_trunc('hour', recorded_at)
            ON CONFLICT (segment_id, hour_bucket) DO UPDATE
              SET avg_speed_kph = EXCLUDED.avg_speed_kph,
                  avg_congestion_level = EXCLUDED.avg_congestion_level
            """
        )
    logger.info("aggregate_past_hour: hourly rollup complete")
