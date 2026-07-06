import datetime
from decimal import Decimal

import pytest

from apps.audit.models import AuditLog, record_audit, verify_chain
from apps.claims import services
from apps.common.enums import AuditAction, ClaimStatus


pytestmark = pytest.mark.django_db


def test_audit_chain_signs_and_verifies(field_officer):
    for i in range(5):
        record_audit(
            entity_type="FRAClaim", entity_id=field_officer.id,
            action=AuditAction.UPDATE, actor=field_officer,
            reason=f"change {i}", previous_state={"v": i}, new_state={"v": i + 1},
        )
    ok, broken = verify_chain()
    assert ok and broken == []
    # each row links to the previous row's signature
    rows = list(AuditLog.objects.order_by("created_at", "id"))
    for prev, cur in zip(rows, rows[1:]):
        assert cur.previous_log_signature == prev.cryptographic_signature


def test_audit_tampering_is_detected(field_officer):
    record_audit(entity_type="X", entity_id=field_officer.id, action=AuditAction.CREATE,
                 actor=field_officer, reason="a", new_state={"v": 1})
    record_audit(entity_type="X", entity_id=field_officer.id, action=AuditAction.UPDATE,
                 actor=field_officer, reason="b", new_state={"v": 2})
    # Tamper with a historical row's content directly in the DB (bypass save()).
    first = AuditLog.objects.order_by("created_at").first()
    AuditLog.objects.filter(pk=first.pk).update(new_state_json={"v": 999})
    ok, broken = verify_chain()
    assert not ok
    assert str(first.id) in broken


def test_audit_log_is_immutable(field_officer):
    entry = record_audit(entity_type="X", entity_id=field_officer.id,
                         action=AuditAction.CREATE, actor=field_officer,
                         reason="r", new_state={})
    entry.reason_text = "changed"
    with pytest.raises(PermissionError):
        entry.save()
    with pytest.raises(PermissionError):
        entry.delete()


def test_reason_required(field_officer):
    with pytest.raises(ValueError):
        record_audit(entity_type="X", entity_id=field_officer.id,
                     action=AuditAction.CREATE, actor=field_officer,
                     reason="   ", new_state={})


def test_claim_lifecycle_appends_chain(field_officer, district, community):
    claim = services.create_claim(
        actor=field_officer, district=district, tribal_community=community,
        claim_type="CFR", area_hectares=Decimal("10.0"),
        claim_date=datetime.date(2024, 1, 1),
    )
    services.transition_claim(claim=claim, to_status=ClaimStatus.SUBMITTED,
                              actor=field_officer, reason="submit")
    actions = list(AuditLog.objects.filter(entity_id=claim.id)
                   .order_by("created_at").values_list("action", flat=True))
    assert actions == [AuditAction.CREATE, AuditAction.TRANSITION]
    assert verify_chain()[0]
