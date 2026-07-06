import datetime
from decimal import Decimal

import pytest

from apps.common.enums import ClaimStatus

pytestmark = pytest.mark.django_db


# ----------------------------------------------------- backup / restore -----
def test_backup_is_real_and_verified(db, district, community):
    from apps.ops.backup import create_backup, restore_logical
    from apps.geo.models import Village
    snap = create_backup()
    assert snap.verified is True
    assert sum(snap.row_counts_json.values()) > 0
    assert snap.storage_key.endswith(".json.gz")

    # simulate loss, then restore
    v = Village.objects.create(village_code="V-LOSS", village_name="X", district=district)
    snap2 = create_backup()
    Village.all_objects.filter(village_code="V-LOSS").hard_delete()
    assert Village.all_objects.filter(village_code="V-LOSS").count() == 0
    restore_logical(snap2)
    assert Village.all_objects.filter(village_code="V-LOSS").count() == 1


def test_snapshot_task_verifies(db):
    from apps.ops.tasks import archive_and_snapshot_data
    result = archive_and_snapshot_data.apply().get()
    assert result["status"] == "ok" and result["verified"] is True


# ------------------------------------------------------------ DPDP -----------
def test_subject_access_export(api):
    resp = api.get("/api/v1/privacy/my-data/")
    assert resp.status_code == 200
    assert resp.data["account"]["id"] == str(api.user.id)


def test_subject_erasure_crypto_erases_pii(admin_api):
    from apps.accounts.models import User
    from apps.audit.models import AuditLog
    target = User.objects.create_user(username="victim", password="StrongPass99!",
                                      phone_number="9990001111")
    resp = admin_api.post("/api/v1/privacy/erase/",
                          {"subject_user_id": str(target.id)}, format="json")
    assert resp.status_code == 200
    target.refresh_from_db()
    assert target.phone_number == "" and target.mfa_secret == ""
    assert target.is_active is False and target.pii_erased_at is not None
    assert target.username.startswith("erased-")
    # erasure event recorded in the audit chain (without PII)
    assert AuditLog.objects.filter(entity_type="User", entity_id=target.id,
                                   action="DELETE").exists()


# -------------------------------------------------- token revocation ---------
def test_logout_revokes_refresh_token(db, roles):
    from rest_framework.test import APIClient
    from apps.accounts.models import User
    User.objects.create_user(username="rev", password="StrongPass99!")
    client = APIClient()
    login = client.post("/api/v1/auth/login/",
                        {"username": "rev", "password": "StrongPass99!"}, format="json")
    refresh = login.data["refresh_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access_token']}")
    # log out (revoke the refresh token)
    out = client.post("/api/v1/auth/logout/", {"refresh_token": refresh}, format="json")
    assert out.status_code == 200
    # the revoked refresh token is now rejected
    after = client.post("/api/v1/auth/refresh/", {"refresh": refresh}, format="json")
    assert after.status_code == 401


# --------------------------------------------------- ML governance -----------
def test_drift_monitor_runs(risk_model, district_with_snapshot):
    from apps.analytics.tasks import monitor_prediction_drift
    result = monitor_prediction_drift.apply().get()
    assert result["status"] in {"ok", "DRIFT_DETECTED", "skipped"}


def test_human_in_the_loop_invariant(api, admin_api, claim_payload):
    """A model/DSS output must never transition a claim. Approval requires an
    authorized human action; analytics endpoints leave status untouched."""
    created = api.post("/api/v1/fra-claims/", claim_payload, format="json").data
    cid = created["id"]
    api.post(f"/api/v1/fra-claims/{cid}/submit/", {"reason": "s"}, format="json")
    admin_api.post(f"/api/v1/fra-claims/{cid}/review/", {"reason": "r"}, format="json")
    # generating DSS recommendations must NOT change claim status
    admin_api.post(f"/api/v1/fra-claims/{cid}/dss-recommendations/", {}, format="json")
    from apps.claims.models import FRAClaim
    assert FRAClaim.objects.get(id=cid).status == ClaimStatus.UNDER_REVIEW


# ------------------------------------------------------- retention -----------
def test_retention_purges_old_soft_deleted(db, district, community):
    from django.utils import timezone
    from apps.claims import services
    from apps.claims.models import FRAClaim
    from apps.ops.tasks import enforce_retention
    claim = services.create_claim(
        actor=None if False else __import__("apps.accounts.models", fromlist=["User"]).User.objects.create_user(username="ret", password="StrongPass99!"),
        district=district, tribal_community=community, claim_type="CFR",
        area_hectares=Decimal("1"), claim_date=datetime.date(2024, 1, 1))
    claim.delete()  # soft delete
    FRAClaim.all_objects.filter(id=claim.id).update(
        soft_deleted_at=timezone.now() - timezone.timedelta(days=365 * 9))
    result = enforce_retention.apply().get()
    assert result["status"] == "ok"
    assert FRAClaim.all_objects.filter(id=claim.id).count() == 0


# --------------------------------------------------- upload hardening --------
def test_upload_rejects_spoofed_content_type(admin_api, field_officer, district, community):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from apps.claims import services
    claim = services.create_claim(
        actor=field_officer, district=district, tribal_community=community,
        claim_type="CFR", area_hectares=Decimal("1"), claim_date=datetime.date(2024, 1, 1))
    # claims to be a PNG but bytes are not -> magic-byte sniff rejects it
    f = SimpleUploadedFile("fake.png", b"not really an image", content_type="image/png")
    resp = admin_api.post(f"/api/v1/fra-claims/{claim.id}/documents/", {"file": f},
                          format="multipart")
    assert resp.status_code == 415
