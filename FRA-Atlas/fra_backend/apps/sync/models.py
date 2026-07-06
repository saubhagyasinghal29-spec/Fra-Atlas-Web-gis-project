"""Server-side records for offline-first mobile sync (spec Task 1.2)."""
from django.db import models

from apps.common.models import BaseModel


class SyncBatch(BaseModel):
    """One push from a field device: bookkeeping + conflict tracking."""
    device_id = models.CharField(max_length=128, db_index=True)
    user_id = models.UUIDField(null=True, blank=True)
    pushed_count = models.PositiveIntegerField(default=0)
    accepted_count = models.PositiveIntegerField(default=0)
    conflict_count = models.PositiveIntegerField(default=0)
    payload_sha256 = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "sync_batch"


class SyncConflict(BaseModel):
    batch = models.ForeignKey(SyncBatch, on_delete=models.CASCADE, related_name="conflicts")
    entity_type = models.CharField(max_length=40)
    client_ref = models.CharField(max_length=128)   # the device's local id
    reason = models.CharField(max_length=200)
    client_payload = models.JSONField(default=dict)

    class Meta:
        db_table = "sync_conflict"
