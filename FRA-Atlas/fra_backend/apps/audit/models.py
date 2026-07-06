"""Immutable, cryptographically chained audit log.

Each row is HMAC-SHA512 signed over (previous_row_signature + canonical content).
This makes the log tamper-evident: altering any historical row breaks every
signature after it, which verify_chain() detects.

Immutability is enforced at the application layer here (save() blocks updates,
delete() is disabled). In production the same table additionally carries a
Postgres rule/trigger rejecting UPDATE/DELETE and a NOT NULL/non-empty CHECK on
reason_text; see README "Audit immutability at the database level".
"""
import hashlib
import hmac
import json
import uuid

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from apps.common.enums import AuditAction


# ---------------------------------------------------------------- signing ----
def canonical_content(payload: dict) -> str:
    """Deterministic JSON used as signing input (sorted keys, no whitespace)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def compute_signature(previous_signature: str, content: str) -> str:
    secret = settings.AUDIT_LOG_SECRET.encode()
    message = f"{previous_signature or ''}{content}".encode()
    return hmac.new(secret, message, hashlib.sha512).hexdigest()


# ------------------------------------------------------------------ model ----
class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.UUIDField(db_index=True)
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField()
    action = models.CharField(max_length=20, choices=AuditAction.choices)
    actor_id = models.UUIDField(null=True, blank=True)
    actor_role = models.CharField(max_length=32)
    previous_state_json = models.JSONField(null=True, blank=True)
    new_state_json = models.JSONField(null=True, blank=True)
    change_diff_json = models.JSONField(null=True, blank=True)
    reason_text = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    created_at = models.DateTimeField()  # set explicitly so it is part of signed content
    cryptographic_signature = models.CharField(max_length=128)
    previous_log_signature = models.CharField(max_length=128, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "audit_log"
        indexes = [
            models.Index(fields=["entity_type", "entity_id", "created_at"]),
            models.Index(fields=["actor_id", "created_at"]),
        ]
        ordering = ["created_at", "id"]

    # ---- immutability guards ----
    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise PermissionError("AuditLog rows are immutable and cannot be updated.")
        if not (self.reason_text or "").strip():
            raise ValueError("AuditLog.reason_text must be a non-empty string.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("AuditLog rows cannot be deleted.")

    def signing_payload(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "previous_state_json": self.previous_state_json,
            "new_state_json": self.new_state_json,
            "change_diff_json": self.change_diff_json,
            "reason_text": self.reason_text,
            "created_at": self.created_at.isoformat(),
        }


# ---------------------------------------------------------------- service ----
def diff_states(previous: dict | None, new: dict | None) -> dict:
    previous = previous or {}
    new = new or {}
    changed = {}
    for key in set(previous) | set(new):
        if previous.get(key) != new.get(key):
            changed[key] = {"from": previous.get(key), "to": new.get(key)}
    return changed


@transaction.atomic
def record_audit(*, entity_type, entity_id, action, actor, reason,
                 previous_state=None, new_state=None, context=None):
    """Append one signed row to the chain. Returns the AuditLog instance."""
    context = context or {}
    last = AuditLog.objects.select_for_update().order_by("-created_at", "-id").first()
    previous_signature = last.cryptographic_signature if last else None

    entry = AuditLog(
        transaction_id=context.get("transaction_id") or uuid.uuid4(),
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_id=getattr(actor, "id", None),
        actor_role=getattr(actor, "designation", "ML_SYSTEM"),
        previous_state_json=previous_state,
        new_state_json=new_state,
        change_diff_json=diff_states(previous_state, new_state),
        reason_text=reason,
        ip_address=context.get("ip_address"),
        user_agent=context.get("user_agent", ""),
        created_at=timezone.now(),
        previous_log_signature=previous_signature,
    )
    entry.cryptographic_signature = compute_signature(
        previous_signature, canonical_content(entry.signing_payload())
    )
    entry.save()
    return entry


def verify_chain():
    """Recompute every signature in order. Returns (ok, list_of_broken_ids)."""
    previous_signature = None
    broken = []
    for row in AuditLog.objects.all().order_by("created_at", "id"):
        expected = compute_signature(
            previous_signature, canonical_content(row.signing_payload())
        )
        if expected != row.cryptographic_signature or row.previous_log_signature != previous_signature:
            broken.append(str(row.id))
        previous_signature = row.cryptographic_signature
    return (len(broken) == 0, broken)
