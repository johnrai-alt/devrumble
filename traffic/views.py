"""
Equivalent of traffic.controller.js + traffic.service.js — powers the
Main Map View. Guests are allowed through (read-only + low-trust), same
as the original requireAuth semantics.
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TrafficReading
from .serializers import TrafficReadingSerializer


class LatestSnapshotView(APIView):
    """
    GET /traffic/?min_lat=&min_lng=&max_lat=&max_lng=

    Returns the latest reading per segment_id, optionally restricted to a
    bounding box (the map viewport) — this is what the Main Map View polls
    on load, and what the WebSocket consumer's tile subscriptions push
    incremental updates for afterwards.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = TrafficReading.objects.all()

        min_lat = request.query_params.get("min_lat")
        min_lng = request.query_params.get("min_lng")
        max_lat = request.query_params.get("max_lat")
        max_lng = request.query_params.get("max_lng")
        if min_lat and min_lng and max_lat and max_lng:
            qs = qs.filter(
                latitude__gte=float(min_lat), latitude__lte=float(max_lat),
                longitude__gte=float(min_lng), longitude__lte=float(max_lng),
            )

        # Latest row per segment_id (requires Postgres — DISTINCT ON).
        latest = qs.order_by("segment_id", "-recorded_at").distinct("segment_id")
        return Response(TrafficReadingSerializer(latest, many=True).data)
