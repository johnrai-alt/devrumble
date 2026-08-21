from rest_framework import serializers

from .models import Incident, IncidentVote


class IncidentSerializer(serializers.ModelSerializer):
    reporterId = serializers.IntegerField(source="reporter_id", read_only=True)

    class Meta:
        model = Incident
        fields = [
            "id", "title", "description", "category", "photo",
            "latitude", "longitude", "status", "credibility_score",
            "expires_at", "created_at", "reporterId",
        ]
        read_only_fields = ["id", "status", "credibility_score", "created_at"]


class IncidentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = ["title", "description", "category", "photo", "latitude", "longitude"]

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("title is required")
        return value


class VoteSerializer(serializers.Serializer):
    value = serializers.IntegerField()

    def validate_value(self, value):
        if value not in (1, -1):
            raise serializers.ValidationError("value must be 1 (upvote) or -1 (downvote)")
        return value
