"""Equivalent of requireVerifiedUser in src/middleware/auth.js."""
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class IsVerifiedUser(BasePermission):
    """
    Blocks guests. Use for voting, and anything else where identity
    actually needs to be real (not just present). Combine with
    IsAuthenticated (DRF checks permissions in order, so list
    IsAuthenticated first) since this assumes request.user is set.
    """

    def has_permission(self, request, view):
        user = request.user
        if not getattr(user, "is_authenticated", False):
            return False
        if user.is_guest:
            raise PermissionDenied("Guest accounts cannot perform this action")
        if not user.email_verified and not user.phone_verified:
            raise PermissionDenied("Please verify your email or phone first")
        return True
