"""
Equivalent of analytics.controller.js + analytics.service.js — powers the
Past Activity Dashboard. Reads only from congestion_hourly_agg (never the
live traffic_readings table), same rationale as the original
aggregationWorker.js comment. One combined endpoint backs the whole
dashboard screen (donut, report snapshots, trend chart) to avoid the
screen needing 3-4 separate round trips.
"""
from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from incidents.models import Incident

from .models import CongestionHourlyAgg
from .serializers import CongestionHourlyAggSerializer, RecentIncidentSerializer

TREND_HOURS = 48
CONGESTION_BUCKETS = [
    ("low", 0.0, 0.34),
    ("medium", 0.34, 0.67),
    ("high", 0.67, 1.01),
]


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        since = timezone.now() - timezone.timedelta(hours=TREND_HOURS)
        recent_agg = CongestionHourlyAgg.objects.filter(hour_bucket__gte=since)

        # Donut: how many hourly-segment buckets fall into each congestion band.
        breakdown = []
        for label, lo, hi in CONGESTION_BUCKETS:
            count = recent_agg.filter(avg_congestion_level__gte=lo, avg_congestion_level__lt=hi).count()
            breakdown.append({"label": label, "count": count})

        # Trend line: average congestion per hour across all segments.
        trend = list(
            recent_agg.values("hour_bucket")
            .annotate(avg_congestion_level=Avg("avg_congestion_level"))
            .order_by("hour_bucket")
        )

        # Report snapshots: counts by status, mirrors incidents module data.
        report_counts = dict(
            Incident.objects.values_list("status").annotate(count=Count("id")).order_by()
        )

        recent_incidents = Incident.objects.order_by("-created_at")[:6]

        return Response({
            "congestionBreakdown": breakdown,
            "trend": trend,
            "reportSnapshots": {
                "active": report_counts.get("active", 0),
                "resolved": report_counts.get("resolved", 0),
                "expired": report_counts.get("expired", 0),
            },
            "recentReports": RecentIncidentSerializer(
                recent_incidents, many=True, context={"request": request}
            ).data,
        })
