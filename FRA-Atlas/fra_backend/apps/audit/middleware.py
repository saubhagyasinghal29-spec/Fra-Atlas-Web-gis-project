"""Attaches a per-request transaction_id + actor context to every request so
audit writes and error envelopes can correlate to a single transaction.
"""
import uuid


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.transaction_id = uuid.uuid4()
        request.audit_context = {
            "transaction_id": request.transaction_id,
            "ip_address": request.META.get("REMOTE_ADDR"),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
        }
        return self.get_response(request)
