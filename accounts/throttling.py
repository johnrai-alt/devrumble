"""
Equivalent of src/middleware/rateLimiter.js.

DRF's SimpleRateThrottle.parse_rate() only reads the *first character* of
the period string (so "300/15m" would NOT mean "300 per 15 minutes" — it
parses as invalid). To match each JS limiter's windowMs/max exactly, each
class here overrides parse_rate() directly with (num_requests, duration_seconds)
instead of relying on the "N/period" string format.
"""
from rest_framework.throttling import SimpleRateThrottle


class _FixedWindowThrottle(SimpleRateThrottle):
    num_requests = 0
    duration_seconds = 0

    def get_rate(self):
        return "unused"  # parse_rate() below ignores this

    def parse_rate(self, rate):
        return (self.num_requests, self.duration_seconds)


class GlobalRateThrottle(_FixedWindowThrottle):
    """globalLimiter: windowMs 15 * 60 * 1000, max 300 — applied to all routes."""
    scope = "global"
    num_requests = 300
    duration_seconds = 15 * 60

    def get_cache_key(self, request, view):
        ident = request.user.sub if getattr(request.user, "is_authenticated", False) else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class OtpRequestThrottle(_FixedWindowThrottle):
    """
    otpRequestLimiter: windowMs 60 * 60 * 1000, max 10 — coarse per-IP
    backstop. The real per-phone 3/hour check lives in accounts/views.py
    (RequestOtpView), same as the JS comment notes it lives in auth.service.js.
    """
    scope = "otp_request"
    num_requests = 10
    duration_seconds = 60 * 60

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class IncidentCreateThrottle(_FixedWindowThrottle):
    """incidentCreateLimiter: windowMs 10 * 60 * 1000, max 20."""
    scope = "incident_create"
    num_requests = 20
    duration_seconds = 10 * 60

    def get_cache_key(self, request, view):
        ident = request.user.sub if getattr(request.user, "is_authenticated", False) else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class VoteThrottle(_FixedWindowThrottle):
    """voteLimiter: windowMs 10 * 60 * 1000, max 60."""
    scope = "vote"
    num_requests = 60
    duration_seconds = 10 * 60

    def get_cache_key(self, request, view):
        ident = request.user.sub if getattr(request.user, "is_authenticated", False) else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
