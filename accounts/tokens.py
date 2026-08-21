"""
Equivalent of src/utils/jwt.js.

Access tokens are real JWTs (short-lived, stateless). Refresh tokens are
opaque random strings, NOT JWTs — we store a hash of them in the DB
(refresh_tokens.token_hash) so individual sessions can be revoked
(logout, logout-all), exactly like the original.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings


def sign_access_token(user) -> str:
    payload = {
        "sub": user.id,
        "isGuest": user.is_guest,
        "emailVerified": user.email_verified,
        "phoneVerified": user.phone_verified,
        "exp": datetime.now(timezone.utc) + settings.JWT_ACCESS_TTL,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_ACCESS_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_access_token(token: str) -> dict:
    # Raises jwt.InvalidTokenError (or a subclass) if invalid/expired,
    # same as the JS jwt.verify() throwing.
    return jwt.decode(token, settings.JWT_ACCESS_SECRET, algorithms=[settings.JWT_ALGORITHM])


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_refresh_token():
    token = secrets.token_hex(48)
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    return token, token_hash, expires_at
