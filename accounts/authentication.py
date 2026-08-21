"""
Equivalent of the `requireAuth` half of src/middleware/auth.js. Runs on
every request (see settings.REST_FRAMEWORK); views that should stay open
to anonymous users use permission_classes = [AllowAny] (the DRF-native
way to express "allow guests through" — matching the original's default
of "no auth required unless a route explicitly adds requireAuth").
"""
import jwt as pyjwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .tokens import verify_access_token


class TokenUser:
    """
    Lightweight stand-in for `req.user` in the JS middleware, which was
    just the raw decoded JWT payload: { sub, isGuest, emailVerified, phoneVerified }.
    Exposes `.is_authenticated` so DRF's IsAuthenticated permission works.
    """

    is_authenticated = True

    def __init__(self, payload: dict):
        self.sub = payload["sub"]
        self.is_guest = payload.get("isGuest", False)
        self.email_verified = payload.get("emailVerified", False)
        self.phone_verified = payload.get("phoneVerified", False)
        self.payload = payload

    def __str__(self):
        return f"user#{self.sub}"


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = request.headers.get("Authorization")
        if not header or not header.startswith("Bearer "):
            # No token presented — same as requireAuth's "pass through as
            # anonymous" for routes that don't require it. Views that DO
            # require auth should set permission_classes=[IsAuthenticated].
            return None

        token = header[len("Bearer "):]
        try:
            payload = verify_access_token(token)
        except pyjwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid or expired access token")

        return (TokenUser(payload), token)
