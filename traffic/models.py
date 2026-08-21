"""
traffic_readings table — matches what workers/ingestWorker.js normalized
into ({ segment_id, source, speed_kph, congestion_level }) and what
workers/aggregationWorker.js reads from (segment_id, recorded_at,
speed_kph, congestion_level). Adds latitude/longitude so the Main Map
View can plot each reading as a point without needing a full PostGIS
line-geometry setup yet.
"""
from django.db import models


class TrafficReading(models.Model):
    segment_id = models.CharField(max_length=64, db_index=True)
    source = models.CharField(max_length=32, default="ingest")
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed_kph = models.FloatField()
    # 0.0 (free-flowing) .. 1.0 (gridlock) — matches how the Main Map View
    # would color-code a marker/segment.
    congestion_level = models.FloatField()
    recorded_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "traffic_readings"
        indexes = [models.Index(fields=["segment_id", "-recorded_at"])]

    def __str__(self):
        return f"{self.segment_id}@{self.recorded_at}"
