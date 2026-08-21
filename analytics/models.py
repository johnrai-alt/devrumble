"""
congestion_hourly_agg table — matches exactly what
workers/aggregationWorker.js's raw SQL INSERT ... ON CONFLICT rolls up
into (segment_id, hour_bucket, avg_speed_kph, avg_congestion_level).
"""
from django.db import models


class CongestionHourlyAgg(models.Model):
    segment_id = models.CharField(max_length=64, db_index=True)
    hour_bucket = models.DateTimeField(db_index=True)
    avg_speed_kph = models.FloatField()
    avg_congestion_level = models.FloatField()

    class Meta:
        db_table = "congestion_hourly_agg"
        unique_together = ("segment_id", "hour_bucket")
        ordering = ["hour_bucket"]

    def __str__(self):
        return f"{self.segment_id}@{self.hour_bucket}"
