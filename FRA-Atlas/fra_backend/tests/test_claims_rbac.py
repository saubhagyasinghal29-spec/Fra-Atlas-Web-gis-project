import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.claims import services
from apps.claims.models import FRAClaim
from apps.common.enums import ClaimStatus


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------- state machine ----
def test_legal_transition_path(field_officer, district_admin, district, community):
    claim = services.create_claim(
        actor=field_officer, district=district, tribal_community=community,
        claim_type="CFR", area_hectares=Decimal("5.0"),
        claim_date=datetime.date(2024, 1, 1),
    )
    services.transition_claim(claim=claim, to_status=ClaimStatus.SUBMITTED,
                              actor=field_officer, reason="submit")
    services.transition_claim(claim=claim, to_status=ClaimStatus.UNDER_REVIEW,
                              actor=district_admin, reason="review")
    services.transition_claim(claim=claim, to_status=ClaimStatus.APPROVED,
                              actor=district_admin, reason="approve")
    claim.refresh_from_db()
    assert claim.status == ClaimStatus.APPROVED
    assert [h["to"] for h in claim.status_history] == ["SUBMITTED", "UNDER_REVIEW", "APPROVED"]


def test_illegal_transition_rejected(field_officer, district, community):
    claim = services.create_claim(
        actor=field_officer, district=district, tribal_community=community,
        claim_type="CFR", area_hectares=Decimal("5.0"),
        claim_date=datetime.date(2024, 1, 1),
    )
    with pytest.raises(ValueError):  # DRAFT -> APPROVED is illegal
        services.transition_claim(claim=claim, to_status=ClaimStatus.APPROVED,
                                  actor=field_officer, reason="skip")


def test_immutable_fields_enforced(field_officer, district, community):
    claim = services.create_claim(
        actor=field_officer, district=district, tribal_community=community,
        claim_type="CFR", area_hectares=Decimal("5.0"),
        claim_date=datetime.date(2024, 1, 1),
    )
    claim.claim_date = datetime.date(2025, 1, 1)
    with pytest.raises(ValidationError):
        claim.save()


def test_direct_status_jump_blocked_at_model(field_officer, district, community):
    claim = services.create_claim(
        actor=field_officer, district=district, tribal_community=community,
        claim_type="CFR", area_hectares=Decimal("5.0"),
        claim_date=datetime.date(2024, 1, 1),
    )
    claim.status = ClaimStatus.APPROVED
    with pytest.raises(ValidationError):
        claim.save()


# ------------------------------------------------------------------ RBAC -----
def test_officer_cannot_create_without_permission(api, claim_payload, district_admin):
    # district_admin lacks CREATE_CLAIM; field officer (api) has it
    resp = api.post("/api/v1/fra-claims/", claim_payload, format="json")
    assert resp.status_code == 201


def test_admin_cannot_create_claim(admin_api, claim_payload):
    resp = admin_api.post("/api/v1/fra-claims/", claim_payload, format="json")
    assert resp.status_code == 403


def test_queryset_scoped_to_jurisdiction(api, field_officer, other_district, community, district):
    # one claim in officer's district, one in another district
    services.create_claim(
        actor=field_officer, district=district, tribal_community=community,
        claim_type="CFR", area_hectares=Decimal("5.0"), claim_date=datetime.date(2024, 1, 1),
    )
    from apps.geo.models import TribalCommunity
    other_comm = TribalCommunity.objects.create(name_english="Other", district=other_district)
    services.create_claim(
        actor=field_officer, district=other_district, tribal_community=other_comm,
        claim_type="CFR", area_hectares=Decimal("5.0"), claim_date=datetime.date(2024, 1, 1),
    )
    resp = api.get("/api/v1/fra-claims/")
    assert resp.status_code == 200
    codes = {c["district_code"] for c in resp.data["results"]}
    assert codes == {"TS-001"}  # other district filtered out


# ------------------------------------------------------------- API flow ------
def test_create_claim_writes_audit(api, claim_payload):
    resp = api.post("/api/v1/fra-claims/", claim_payload, format="json")
    assert resp.status_code == 201
    from apps.audit.models import AuditLog
    assert AuditLog.objects.filter(entity_id=resp.data["id"], action="CREATE").exists()


def test_approve_requires_permission(admin_api, api, claim_payload):
    created = api.post("/api/v1/fra-claims/", claim_payload, format="json").data
    cid = created["id"]
    # walk to UNDER_REVIEW as the right actors
    api.post(f"/api/v1/fra-claims/{cid}/submit/", {"reason": "s"}, format="json")
    admin_api.post(f"/api/v1/fra-claims/{cid}/review/", {"reason": "r"}, format="json")
    # field officer cannot approve
    forbidden = api.post(f"/api/v1/fra-claims/{cid}/approve/", {"reason": "a"}, format="json")
    assert forbidden.status_code == 403
    # admin can
    ok = admin_api.post(f"/api/v1/fra-claims/{cid}/approve/", {"reason": "a"}, format="json")
    assert ok.status_code == 200 and ok.data["status"] == "APPROVED"
