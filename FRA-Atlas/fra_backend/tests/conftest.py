import datetime
import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.bootstrap import seed_role_permissions
from apps.accounts.models import User
from apps.common.enums import ClaimType, Designation
from apps.geo.models import District, TribalCommunity


@pytest.fixture
def roles(db):
    seed_role_permissions()


@pytest.fixture
def district(db):
    return District.objects.create(
        district_code="TS-001", name_english="Test District", state="Telangana",
        tribal_population=100000,
    )


@pytest.fixture
def other_district(db):
    return District.objects.create(
        district_code="MH-001", name_english="Other District", state="Maharashtra",
    )


@pytest.fixture
def community(db, district):
    return TribalCommunity.objects.create(name_english="Test Tribe", district=district)


@pytest.fixture
def field_officer(db, roles, district):
    return User.objects.create_user(
        username="officer", password="TestPass123!",
        designation=Designation.FIELD_OFFICER,
        assigned_states=["Telangana"], assigned_districts=["TS-001"],
    )


@pytest.fixture
def district_admin(db, roles, district):
    return User.objects.create_user(
        username="admin", password="TestPass123!",
        designation=Designation.DISTRICT_ADMIN,
        assigned_states=["Telangana"], assigned_districts=["TS-001"],
    )


@pytest.fixture
def api(field_officer):
    client = APIClient()
    client.force_authenticate(user=field_officer)
    client.user = field_officer
    return client


@pytest.fixture
def admin_api(district_admin):
    client = APIClient()
    client.force_authenticate(user=district_admin)
    client.user = district_admin
    return client


@pytest.fixture
def claim_payload(district, community):
    return {
        "district": str(district.id),
        "tribal_community": str(community.id),
        "claim_type": ClaimType.COMMUNITY_FOREST,
        "area_hectares": "100.50",
        "claim_date": str(datetime.date(2024, 6, 15)),
        "reason": "Initial submission",
    }


@pytest.fixture
def risk_model(db):
    """Train a tiny real RandomForest, export ONNX + joblib, register active model."""
    import io
    import numpy as np
    import joblib
    from sklearn.ensemble import RandomForestRegressor
    from skl2onnx import to_onnx
    from apps.analytics.inference import FEATURE_LIST, clear_predictor_cache, onnx_signature
    from apps.analytics.models import RiskPredictionModel

    rng = np.random.default_rng(0)
    X = rng.random((60, len(FEATURE_LIST))).astype("float32")
    # synthetic target: higher when approval rate (col 0) is low
    y = (80 - X[:, 0] * 60 + X[:, 3] * 10).astype("float32")
    model = RandomForestRegressor(n_estimators=40, max_depth=6, random_state=0).fit(X, y)
    onnx_bytes = to_onnx(model, X[:1]).SerializeToString()
    buf = io.BytesIO(); joblib.dump(model, buf)
    clear_predictor_cache()
    return RiskPredictionModel.objects.create(
        version="test-1.0", is_active=True, feature_list=FEATURE_LIST,
        model_binary_blob=onnx_bytes, explainer_blob=buf.getvalue(),
        signature_sha256=onnx_signature(onnx_bytes),
        feature_importance_json={}, deployed_at=__import__("django.utils.timezone",
            fromlist=["now"]).now(),
    )


@pytest.fixture
def snapshot_factors():
    return {
        "Approval Rate": 0.42, "Pending Claims Rate": 0.43, "Avg Processing Time": 118.0,
        "Forest Loss Rate": 2.1, "Tribal Pop. Coverage": 0.035, "CFR Recognition Rate": 0.15,
        "Rejection Rate": 0.14, "Encroachment Density": 0.35,
    }


@pytest.fixture
def district_with_snapshot(db, district, snapshot_factors):
    from django.utils import timezone
    from apps.analytics.models import DistrictRiskSnapshot
    DistrictRiskSnapshot.objects.create(
        district=district, risk_score=70, risk_category="CRITICAL",
        factors_json=snapshot_factors, prediction_timestamp=timezone.now(),
    )
    return district


@pytest.fixture(autouse=True)
def eager_celery(settings):
    """Run Celery tasks in-process during tests so .delay() works without a broker."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    from config.celery import app
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = False
    app.conf.broker_url = "memory://"
    app.conf.result_backend = "cache+memory://"
    yield
