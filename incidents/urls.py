"""Equivalent of incidents.routes.js."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.IncidentListCreateView.as_view()),
    path("<int:pk>/", views.IncidentDetailView.as_view()),
    path("<int:pk>/vote", views.IncidentVoteView.as_view()),
]
