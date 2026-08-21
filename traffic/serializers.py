from rest_framework import serializers

from .models import TrafficReading


class TrafficReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficReading
        fields = [
            "segment_id", "source", "latitude", "longitude",
            "speed_kph", "congestion_level", "recorded_at",
        ]
