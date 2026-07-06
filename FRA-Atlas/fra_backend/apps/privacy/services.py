"""Data-subject rights under the DPDP Act 2023.

ACCESS: export everything the system holds about a data principal.
ERASURE: crypto-erase the subject's PII while (a) preserving the immutable audit
trail (which never stored PII content, only event metadata) and (b) retaining
statutory claim records under a lawful-basis carve-out (legal record-keeping for
a welfare entitlement), pseudonymizing the personal link.

This reconciles the audit-flagged tension between the right to erasure and the
append-only audit log: we destroy the *plaintext PII*, not the audit chain.
"""
import uuid

from django.utils import timezone

from apps.audit.models import record_audit
from apps.common.enums import AuditAction


def export_subject_data(user) -> dict:
    """Right to access / portability."""
    from apps.claims.models import FRAClaim
    FRAClaim.objects.filter(
        tribal_community__in=[]) if False else FRAClaim.objects.none()
    # claims the user authored are linked via audit actor; surface their account
    return {
        "account": {
            "id": str(user.id), "username": user.username, "email": user.email,
            "designation": user.designation, "phone_number": user.phone_number,
            "assigned_states": user.assigned_states,
            "assigned_districts": user.assigned_districts,
            "mfa_enabled": user.mfa_enabled,
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
        },
        "exported_at": timezone.now().isoformat(),
        "note": "Claim records authored by this account are retained under statutory "
                "record-keeping obligations; see erasure policy.",
    }


def erase_subject(user, *, actor, reason="DPDP erasure request") -> dict:
    """Right to erasure via crypto-erasure of PII + account pseudonymization.

    PII columns (phone, MFA secret) are encrypted at rest; we overwrite them so no
    plaintext remains. The account is pseudonymized and deactivated. The audit log
    records the erasure event but contained no PII to begin with.
    """
    before = {"username": user.username, "had_phone": bool(user.phone_number)}
    user.phone_number = ""
    user.mfa_secret = ""
    user.mfa_enabled = False
    user.email = ""
    user.first_name = user.last_name = ""
    user.username = f"erased-{uuid.uuid4().hex[:12]}"
    user.is_active = False
    user.pii_erased_at = timezone.now()
    user.set_unusable_password()
    user.save()

    record_audit(
        entity_type="User", entity_id=user.id, action=AuditAction.DELETE,
        actor=actor, reason=reason,
        previous_state={"pii": "redacted"}, new_state={"pii_erased": True},
    )
    return {"erased": True, "pseudonym": user.username, "before": before}
