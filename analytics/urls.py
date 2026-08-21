"""Equivalent of analytics.routes.js."""
from django.urls import path

from . import views

urlpatterns = [
    path("dashboard", views.DashboardSummaryView.as_view()),
]
