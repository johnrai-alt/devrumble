"""Equivalent of auth.routes.js."""
from django.urls import path

from . import views

urlpatterns = [
    path("register", views.RegisterView.as_view()),
    path("login", views.LoginView.as_view()),

    path("otp/request", views.RequestOtpView.as_view()),
    path("otp/verify", views.VerifyOtpView.as_view()),

    path("guest", views.GuestLoginView.as_view()),
    path("upgrade-guest", views.UpgradeGuestView.as_view()),  # requireAuth

    path("refresh", views.RefreshView.as_view()),
    path("logout", views.LogoutView.as_view()),
    path("logout-all", views.LogoutAllView.as_view()),  # requireAuth

    path("me", views.MeView.as_view()),  # requireAuth — powers the User Profile screen
]
