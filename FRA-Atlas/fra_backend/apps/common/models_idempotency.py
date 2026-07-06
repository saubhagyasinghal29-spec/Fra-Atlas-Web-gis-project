"""Durable idempotency store (DB-backed; swap to Redis with a TTL in prod)."""
import uuid

from django.db import models


class IdempotencyRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=200, db_index=True)
    user_id = models.UUIDField(null=True, blank=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    response_status = models.PositiveIntegerField()
    response_body = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "idempotency_record"
        unique_together = ("key", "user_id")
