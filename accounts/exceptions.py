"""
Equivalent of src/middleware/errorHandler.js.

In the JS version, `service.js` throws `new Error(msg)` with a `.status`
property attached, `asyncHandler` forwards it to Express's `next(err)`,
and `errorHandler` renders `{ error: message }` with that status (masking
the message as "Internal server error" for uncaught 500s).

Here, views raise AppError(message, status) directly; DRF's exception
handling pipeline calls app_exception_handler for every view (function-
based or class-based) automatically — there's no need for an asyncHandler
equivalent since DRF already wraps view dispatch in try/except.
"""
import logging

from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status as http_status

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Raise AppError('message', status) from a view — mirrors:
    const err = new Error('message'); err.status = status; throw err;
    """

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def app_exception_handler(exc, context):
    if isinstance(exc, AppError):
        return Response({"error": exc.message}, status=exc.status)

    # Let DRF handle its own exceptions (validation errors, throttling,
    # authentication failures, 404s) with its normal formatting first.
    response = drf_exception_handler(exc, context)
    if response is not None:
        # Normalize DRF's default {"detail": "..."} shape to {"error": "..."}
        # to match the original API contract.
        detail = response.data.get("detail", response.data) if isinstance(response.data, dict) else response.data
        response.data = {"error": str(detail)}
        return response

    # Anything else is an uncaught 500 — same masking as errorHandler.js.
    logger.error("Unhandled exception", exc_info=exc)
    return Response({"error": "Internal server error"}, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
