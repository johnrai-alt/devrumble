"""
Backs the bottom-nav "search" tab. Assumption: search scope is incidents
only for now (title/description match) — extend to traffic segments or
routing once those modules have real queryable data.
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Incident
from .serializers import IncidentSerializer


class SearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response([])

        qs = Incident.objects.filter(title__icontains=query) | Incident.objects.filter(
            description__icontains=query
        )
        return Response(IncidentSerializer(qs.distinct(), many=True, context={"request": request}).data)
