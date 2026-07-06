import datetime

import pyotp
import pytest
from django.db import connection
from rest_framework.test import APIClient

from apps.accounts.models import LOCKOUT_THRESHOLD, User
from apps.common.enums import Designation

pytestmark = pytest.mark.django_db


# -------------------------------------------------------- PII encryption -----
def test_pii_encrypted_at_rest(db):
    u = User.objects.create_user(username="p", password="x", phone_number="9998887777")
    with connection.cursor() as c:
        c.execute("SELECT phone_number FROM account_user WHERE username='p'")
        raw = c.fetchone()[0]
    assert raw.startswith("v1:") and "9998887777" not in raw      # encrypted on disk
    assert User.objects.get(username="p").phone_number == "9998887777"  # decrypted on read


def test_encryption_roundtrip_helpers():
    from apps.common.encryption import decrypt, encrypt
    token = encrypt("secret-value")
    assert token != "secret-value" and decrypt(token) == "secret-value"
    assert encrypt("") == ""  # empties pass through


# -------------------------------------------------------------- login --------
def test_login_success_returns_tokens(db, roles):
    User.objects.create_user(username="u", password="TestPass123!",
                             designation=Designation.FIELD_OFFICER)
    resp = APIClient().post("/api/v1/auth/login/",
                            {"username": "u", "password": "TestPass123!"}, format="json")
    assert resp.status_code == 200
    assert "access_token" in resp.data and "refresh_token" in resp.data


def test_login_lockout_after_five_failures(db):
    User.objects.create_user(username="lock", password="right")
    client = APIClient()
    for _ in range(LOCKOUT_THRESHOLD):
        r = client.post("/api/v1/auth/login/", {"username": "lock", "password": "wrong"},
                        format="json")
        assert r.status_code == 401
    # 6th attempt -- even with correct password -- is locked out
    r = client.post("/api/v1/auth/login/", {"username": "lock", "password": "right"},
                    format="json")
    assert r.status_code == 423


# --------------------------------------------------------------- MFA ---------
def test_mfa_challenge_then_verify(db, roles):
    user = User.objects.create_user(username="m", password="pw",
                                    designation=Designation.FIELD_OFFICER)
    user.mfa_enabled = True
    user.mfa_secret = pyotp.random_base32()
    user.save()
    client = APIClient()
    login = client.post("/api/v1/auth/login/", {"username": "m", "password": "pw"},
                        format="json")
    assert login.status_code == 202 and login.data["mfa_required"]
    challenge = login.data["mfa_challenge"]

    code = pyotp.TOTP(user.mfa_secret).now()
    ok = client.post("/api/v1/auth/mfa-verify/",
                     {"mfa_challenge": challenge, "otp_code": code}, format="json")
    assert ok.status_code == 200 and "access_token" in ok.data

    bad = client.post("/api/v1/auth/mfa-verify/",
                      {"mfa_challenge": challenge, "otp_code": "000000"}, format="json")
    assert bad.status_code == 401


def test_mfa_setup_returns_provisioning_uri(api):
    resp = api.post("/api/v1/auth/mfa-setup/", {}, format="json")
    assert resp.status_code == 200
    assert resp.data["provisioning_uri"].startswith("otpauth://")
    api.user.refresh_from_db()
    assert api.user.mfa_enabled is True


# ------------------------------------------------------- idempotency ---------
def test_idempotency_key_dedupes_creation(api, claim_payload):
    headers = {"HTTP_IDEMPOTENCY_KEY": "abc-123"}
    r1 = api.post("/api/v1/fra-claims/", claim_payload, format="json", **headers)
    r2 = api.post("/api/v1/fra-claims/", claim_payload, format="json", **headers)
    assert r1.status_code == 201
    assert r1.data["id"] == r2.data["id"]            # same object returned
    assert r2.has_header("Idempotent-Replay")
    from apps.claims.models import FRAClaim
    assert FRAClaim.objects.count() == 1             # only one claim created


# -------------------------------------------------------------- ETag ---------
def test_etag_optimistic_locking(api, claim_payload):
    created = api.post("/api/v1/fra-claims/", claim_payload, format="json")
    cid = created.data["id"]
    detail = api.get(f"/api/v1/fra-claims/{cid}/")
    etag = detail["ETag"]
    # stale ETag is rejected
    stale = api.patch(f"/api/v1/fra-claims/{cid}/", {"area_hectares": "5"},
                      format="json", HTTP_IF_MATCH="deadbeef")
    assert stale.status_code == 412
    # correct ETag passes precondition
    ok = api.patch(f"/api/v1/fra-claims/{cid}/", {"area_hectares": "5"},
                   format="json", HTTP_IF_MATCH=etag)
    assert ok.status_code == 200
