"""
Equivalent of src/workers/ingestWorker.js.

Polls a third-party traffic provider (Google Roads/Directions API, HERE,
TomTom) on an interval and normalizes results into traffic_readings.
Runs as a Celery worker process, scheduled by Celery Beat (see
sadaksathi/celery.py) — same "never blocks user-facing request handling"
rationale as the original comment.
"""
import logging
import requests
from celery import shared_task
from django.conf import settings
from django.contrib.gis.geos import Point
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import TrafficReading

@shared_task
def poll_traffic_provider():
    """Fetch live traffic data and broadcast updates over WebSockets."""
    api_key = os.getenv("GOOGLE_TRAFFIC_API_KEY")
    if not api_key:
        return "API key missing"

    # Example integration fetching provider flow/congestion data
    url = f"https://maps.googleapis.com/maps/api/traffic/json?key={api_key}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        channel_layer = get_channel_layer()

        for segment in data.get("segments", []):
            lat = segment["location"]["lat"]
            lng = segment["location"]["lng"]
            congestion_level = segment["congestion_level"]

            reading = TrafficReading.objects.create(
                location=Point(lng, lat, srid=4326),
                congestion_level=congestion_level
            )

            # Broadcast live map tile reading to websocket group
            async_to_sync(channel_layer.group_send)(
                "traffic_updates",
                {
                    "type": "traffic_tile_update",
                    "data": {
                        "id": reading.id,
                        "lat": lat,
                        "lng": lng,
                        "congestion": congestion_level
                    }
                }
            )
    return "Traffic polled and broadcasted successfully."

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="traffic.tasks.poll_traffic_provider")
def poll_traffic_provider():
    # TODO:
    # 1. Fetch congestion data for the city's bounding box from the provider
    # 2. Normalize into { segment_id, source, speed_kph, congestion_level }
    # 3. Insert into traffic_readings (via traffic/models.py once defined)
    # 4. Cache latest snapshot in Redis (django.core.cache) for fast map reads
    logger.info("poll_traffic_provider: polling traffic provider (not yet implemented)")
