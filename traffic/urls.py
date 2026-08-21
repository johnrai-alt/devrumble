"""Equivalent of traffic.routes.js."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.LatestSnapshotView.as_view()),
]
