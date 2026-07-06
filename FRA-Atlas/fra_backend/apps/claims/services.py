"""Business operations for FRA claims. Every mutation is wrapped in a DB
transaction together with an audit-chain append, so a claim change and its
audit record commit or roll back as one unit.
"""
from django.db import transaction
from django.utils import timezone

from apps.audit.models import record_audit
from apps.claims.models import FRAClaim
from apps.common.enums import AuditAction, ClaimStatus


def _snapshot(claim: FRAClaim) -> dict:
    return {
        "id": str(claim.id),
        "claim_identifier": claim.claim_identifier,
        "status": claim.status,
        "claim_type": claim.claim_type,
        "area_hectares": str(claim.area_hectares),
        "district_code": claim.district_code,
        "tribal_community_id": str(claim.tribal_community_id),
    }


def _generate_identifier(district_code: str) -> str:
    FRAClaim.all_objects.filter(district=None).count()  # placeholder safeguard
    count = FRAClaim.all_objects.filter(claim_identifier__startswith=district_code).count()
    return f"{district_code}-{count + 1:05d}-{timezone.now():%Y}"


@transaction.atomic
def create_claim(*, actor, district, tribal_community, claim_type, area_hectares,
                 claim_date, village=None, forest_location_geojson=None,
                 reason="Initial creation", context=None):
    claim = FRAClaim(
        claim_identifier=_generate_identifier(district.district_code),
        claim_type=claim_type,
        status=ClaimStatus.DRAFT,
        district=district,
        tribal_community=tribal_community,
        village=village,
        area_hectares=area_hectares,
        claim_date=claim_date,
        forest_location_geojson=forest_location_geojson,
        status_history=[],
    )
    claim.full_clean(exclude=["status_history"])
    claim.save()
    record_audit(
        entity_type="FRAClaim", entity_id=claim.id, action=AuditAction.CREATE,
        actor=actor, reason=reason, previous_state=None,
        new_state=_snapshot(claim), context=context,
    )
    return claim


@transaction.atomic
def transition_claim(*, claim: FRAClaim, to_status, actor, reason, context=None):
    if not reason or not reason.strip():
        raise ValueError("A non-empty reason is required for every transition.")
    if not claim.can_transition_to(to_status):
        raise ValueError(f"Illegal transition {claim.status} -> {to_status}")

    before = _snapshot(claim)
    from_status = claim.status
    claim.status = to_status
    claim.status_history = (claim.status_history or []) + [{
        "from": from_status,
        "to": to_status,
        "at": timezone.now().isoformat(),
        "by": str(getattr(actor, "id", "system")),
        "reason": reason,
    }]
    claim.save()

    action = {
        ClaimStatus.APPROVED: AuditAction.APPROVE,
        ClaimStatus.REJECTED: AuditAction.REJECT,
    }.get(to_status, AuditAction.TRANSITION)
    record_audit(
        entity_type="FRAClaim", entity_id=claim.id, action=action,
        actor=actor, reason=reason, previous_state=before,
        new_state=_snapshot(claim), context=context,
    )
    return claim
