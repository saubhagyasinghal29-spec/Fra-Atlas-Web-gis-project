"""Standardized API error envelope (spec Phase 2, error response format)."""
from rest_framework.views import exception_handler


def standardized_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response
    request = context.get("request")
    request_id = getattr(request, "transaction_id", None)

    code = exc.__class__.__name__.replace("Error", "").upper() or "ERROR"
    detail = response.data
    message = detail.get("detail") if isinstance(detail, dict) and "detail" in detail else "Request failed"
    field_errors = detail if isinstance(detail, dict) and "detail" not in detail else {}

    response.data = {
        "error_code": code,
        "message": str(message),
        "details": {"field_errors": field_errors},
        "request_id": str(request_id) if request_id else None,
    }
    return response
