from rest_framework import serializers

from incidents.models import Incident

from .models import CongestionHourlyAgg


class CongestionHourlyAggSerializer(serializers.ModelSerializer):
    class Meta:
        model = CongestionHourlyAgg
        fields = ["segment_id", "hour_bucket", "avg_speed_kph", "avg_congestion_level"]


class RecentIncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ["id", "title", "category", "photo", "status", "created_at"]
