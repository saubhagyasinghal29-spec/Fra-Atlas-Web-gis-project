"""Cross-cutting API hardening: idempotency keys, ETag optimistic locking,
role-aware throttling, and structured request logging.
"""
import hashlib
import json
import logging
import time

from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from apps.common.models_idempotency import IdempotencyRecord

logger = logging.getLogger("fra.requests")


# ----------------------------------------------------------- idempotency ----
class IdempotencyMixin:
    """Honor an Idempotency-Key header on unsafe methods. The first request is
    processed and its response stored; replays return the stored response.
    Apply by overriding create() to call `self.idempotent(request, super().create)`.
    """

    idempotency_methods = {"POST"}

    def idempotent(self, request, handler, *args, **kwargs):
        key = request.headers.get("Idempotency-Key")
        if not key or request.method not in self.idempotency_methods:
            return handler(request, *args, **kwargs)

        user_id = getattr(request.user, "id", None)
        existing = IdempotencyRecord.objects.filter(key=key, user_id=user_id).first()
        if existing:
            return Response(existing.response_body, status=existing.response_status,
                            headers={"Idempotent-Replay": "true"})

        response = handler(request, *args, **kwargs)
        if 200 <= response.status_code < 300:
            import json

            from rest_framework.utils.encoders import JSONEncoder
            safe_body = json.loads(json.dumps(response.data, cls=JSONEncoder))
            IdempotencyRecord.objects.get_or_create(
                key=key, user_id=user_id,
                defaults={"method": request.method, "path": request.path,
                          "response_status": response.status_code,
                          "response_body": safe_body},
            )
        return response


# ------------------------------------------------------------------ ETag -----
def make_etag(instance) -> str:
    basis = f"{instance.pk}:{instance.updated_at.isoformat()}"
    return hashlib.sha256(basis.encode()).hexdigest()[:32]


class ETagMixin:
    """Adds an ETag to retrieve responses and enforces If-Match on updates."""

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        response["ETag"] = make_etag(self.get_object())
        return response

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if_match = request.headers.get("If-Match")
        if if_match and if_match != make_etag(instance):
            return Response(
                {"detail": "Resource was modified by another request (stale ETag)."},
                status=status.HTTP_412_PRECONDITION_FAILED,
            )
        return super().update(request, *args, **kwargs)


# -------------------------------------------------------------- throttling ---
class RoleRateThrottle(UserRateThrottle):
    """Per-user rate that scales with role: field staff get a lower ceiling than
    state coordinators / superusers."""

    RATE_BY_ROLE = {
        "SUPERUSER": "5000/min",
        "STATE_COORDINATOR": "3000/min",
        "DISTRICT_ADMIN": "2000/min",
        "BLOCK_OFFICIAL": "1000/min",
        "FIELD_OFFICER": "1000/min",
    }

    def get_rate(self):
        return "1000/min"

    def allow_request(self, request, view):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            self.rate = self.RATE_BY_ROLE.get(getattr(user, "designation", ""), "1000/min")
            self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)


# --------------------------------------------------------- request logging ---
class RequestLoggingMiddleware:
    """Emit one structured JSON log line per request (metadata only -- never the
    request/response body, to avoid leaking PII)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        try:
            logger.info(json.dumps({
                "request_id": str(getattr(request, "transaction_id", "")),
                "method": request.method,
                "path": request.path,
                "user_id": str(getattr(getattr(request, "user", None), "id", "")),
                "status": getattr(response, "status_code", None),
                "latency_ms": latency_ms,
            }))
        except Exception:  # logging must never break the request
            pass
        return response
