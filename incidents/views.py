"""
Equivalent of incidents.controller.js + incidents.service.js — powers the
Blog Feed. Reporting is a "low-trust write" (guests allowed, same as the
original requireAuth note); voting requires a verified identity
(requireVerifiedUser), same as the original middleware split.
"""
from datetime import timedelta

from django.db import IntegrityError
from django.db.models import Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.exceptions import AppError
from accounts.models import User
from accounts.permissions import IsVerifiedUser
from accounts.throttling import IncidentCreateThrottle, VoteThrottle

from .models import Incident, IncidentVote
from .serializers import IncidentCreateSerializer, IncidentSerializer, VoteSerializer

DEFAULT_INCIDENT_TTL_HOURS = 24


class IncidentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # GET /incidents/?category=&status=active (Blog Feed "events" tab)
        qs = Incident.objects.all()

        category = request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)

        status_param = request.query_params.get("status", "active")
        if status_param:
            qs = qs.filter(status=status_param)

        return Response(IncidentSerializer(qs, many=True, context={"request": request}).data)

    def post(self, request):
        throttle = IncidentCreateThrottle()
        if not throttle.allow_request(request, self):
            raise AppError("Too many incident reports. Slow down.", 429)

        serializer = IncidentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reporter = User.objects.filter(pk=request.user.sub).first()
        incident = serializer.save(
            reporter=reporter,
            expires_at=timezone.now() + timedelta(hours=DEFAULT_INCIDENT_TTL_HOURS),
        )
        return Response(
            IncidentSerializer(incident, context={"request": request}).data, status=201
        )


class IncidentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        incident = Incident.objects.filter(pk=pk).first()
        if not incident:
            raise AppError("Incident not found", 404)
        return Response(IncidentSerializer(incident, context={"request": request}).data)


class IncidentVoteView(APIView):
    permission_classes = [IsAuthenticated, IsVerifiedUser]

    def post(self, request, pk):
        throttle = VoteThrottle()
        if not throttle.allow_request(request, self):
            raise AppError("Too many votes. Slow down.", 429)

        incident = Incident.objects.filter(pk=pk).first()
        if not incident:
            raise AppError("Incident not found", 404)

        serializer = VoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        value = serializer.validated_data["value"]

        user = User.objects.get(pk=request.user.sub)
        IncidentVote.objects.update_or_create(
            incident=incident, user=user, defaults={"value": value}
        )

        incident.credibility_score = (
            IncidentVote.objects.filter(incident=incident).aggregate(total=Sum("value"))["total"] or 0
        )
        incident.save(update_fields=["credibility_score"])

        return Response(IncidentSerializer(incident, context={"request": request}).data)
