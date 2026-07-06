"""Audit-log integrity verification job (spec Phase 3, task e)."""
import time

from celery import shared_task
from django.utils import timezone

from apps.audit.models import AuditLog, verify_chain


@shared_task(bind=True)
def verify_audit_log_integrity(self):
    """Recompute the HMAC chain; stamp verified_at on success, flag tampering."""
    started = time.monotonic()
    ok, broken = verify_chain()
    total = AuditLog.objects.count()
    if ok:
        # mark unverified rows as verified (bulk, bypassing immutability guard
        # intentionally: verified_at is metadata, not signed content)
        AuditLog.objects.filter(verified_at__isnull=True).update(verified_at=timezone.now())
    return {
        "status": "ok" if ok else "TAMPERING_DETECTED",
        "rows_total": total,
        "broken_row_ids": broken,
        "duration_s": round(time.monotonic() - started, 2),
    }
