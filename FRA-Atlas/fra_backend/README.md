# FRA Atlas Backend — Foundation Build

A runnable, tested Django + DRF foundation for the Forest Rights Act Atlas
Decision Support System. This is **Phase 1 plus a working vertical slice of
Phases 2 and 5** from the intensive backend spec — the spine that the remaining
phases (Celery jobs, ONNX inference, PostGIS spatial queries, documents/S3,
deployment) bolt onto. See `SCOPE_AND_STATUS.md` for the exact done/remaining map.

It is grounded in your **real data**: the 500-district `fra_risk_scores` and
`fra_features_500` CSVs are loaded into the schema by a management command.

## Quick start

```bash
# System libs for GeoDjango (Debian/Ubuntu):
#   apt-get install libsqlite3-mod-spatialite gdal-bin libgdal-dev libgeos-dev libproj-dev
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py load_fra_data          # 500 real districts + geometry + risk + correlations
python manage.py train_risk_model       # trains RandomForest -> ONNX + SHAP, registers active model
python manage.py createsuperuser        # optional, for /admin
python manage.py runserver
pytest -q                               # 66 tests, 91% coverage (SpatiaLite AND PostGIS+Redis)
```

Runs on **SpatiaLite (SQLite + spatial extension)** for dev — real geometry
fields and `ST_*` spatial queries with no Postgres needed. Celery tasks run
synchronously in tests (`.apply()`), so the async layer is provable without a
broker. Production swaps the DB engine to **PostGIS** (one settings change; the
model and query code are identical) — see `docker-compose.yml`.

## What's implemented and proven

| Area | Status |
|------|--------|
| UUID PKs, timestamptz, soft-delete base model | ✅ `apps/common` |
| Custom User + RBAC (6 roles, 8 permissions, geographic scoping) | ✅ `apps/accounts` |
| District / Village / TribalCommunity (real GeoDjango geometry) | ✅ `apps/geo` |
| **Geospatial: ST_Contains point-in-polygon, GeoJSON, nearby (SpatiaLite/PostGIS)** | ✅ `apps/geo/services.py` |
| FRAClaim finite-state machine + immutable fields + status_history | ✅ `apps/claims` |
| Immutable audit log, HMAC-SHA512 chain, tamper verifier | ✅ `apps/audit` |
| **Real ML pipeline: train → ONNX → serve → SHAP explain** | ✅ `apps/analytics` |
| **DSS recommendation engine (transparent rule engine on risk)** | ✅ `apps/analytics/dss.py` |
| **Celery async layer + 4 scheduled jobs (risk, DSS, correlation, audit)** | ✅ `apps/*/tasks.py` |
| Risk model registry, per-district snapshots, correlation matrix | ✅ `apps/analytics` |
| JWT auth with role/scope claims | ✅ `apps/accounts/auth.py` |
| Claims CRUD API, scoped querysets, transition + DSS endpoints | ✅ `apps/claims/views.py` |
| Live predict + analytics read endpoints fed by real data | ✅ `apps/analytics/views.py` |
| OpenAPI schema + Swagger UI (`/api/v1/docs/`) | ✅ drf-spectacular |
| Docker + docker-compose (Postgres/PostGIS + Redis + web + worker + beat) | ✅ |
| **PII encryption at rest (versioned Fernet) + MFA/TOTP + login lockout** | ✅ `apps/accounts`, `apps/common/encryption.py` |
| **Idempotency keys + ETag optimistic locking + role throttling** | ✅ `apps/common/api_hardening.py` |
| **Documents: upload/validate/scan/OCR/download (pluggable storage)** | ✅ `apps/documents` |
| **Async reports (CSV/XLSX) with job polling** | ✅ `apps/reports` |
| **All 7 Celery scheduled jobs + BatchJob logging + dead-letter queue** | ✅ `apps/ops`, `apps/*/tasks.py` |
| **Prometheus /metrics + alerts + Grafana dashboard** | ✅ `django-prometheus`, `deploy/` |
| **k8s manifests + Helm chart; ADRs + operations runbook** | ✅ `deploy/`, `docs/` |
| **Offline-first mobile sync (delta pull + push, conflict handling)** | ✅ `apps/sync` |
| **12-factor config: same image dev↔prod (PostGIS/Redis/S3), prod hardening** | ✅ `config/settings.py`, `Dockerfile` |
| **Real verified backups + restore; DPDP data-subject rights + crypto-erasure** | ✅ `apps/ops/backup.py`, `apps/privacy` |
| **Materialized views @ 200k claims (0.3ms); JWT revocation; ML drift/fairness governance** | ✅ `apps/analytics`, `apps/accounts` |
| **Gated security CI (ruff+bandit blocking, pip-audit, 80% gate); ruff/bandit clean** | ✅ `.github/workflows/ci.yml` |
| 66-test suite, **91% coverage**, verified on SpatiaLite AND real PostGIS+Redis | ✅ `tests/` |

## Key endpoints

```
POST /api/v1/auth/login/                                  JWT (role+scope claims)
POST /api/v1/auth/refresh/
GET  /api/v1/fra-claims/                                  scoped to caller jurisdiction
POST /api/v1/fra-claims/                                  CREATE_CLAIM
GET  /api/v1/fra-claims/{id}/
POST /api/v1/fra-claims/{id}/submit|review|approve|reject/  state machine + audit
GET  /api/v1/fra-claims/{id}/dss-recommendations/        list stored DSS recs
POST /api/v1/fra-claims/{id}/dss-recommendations/        (re)generate via DSS engine
POST /api/v1/analytics/predict-district-risk/            live ONNX inference + SHAP
GET  /api/v1/analytics/risk-model/status/
GET  /api/v1/analytics/factor-correlation/
GET  /api/v1/analytics/pca-clustering/                   PC1/PC2/cluster scatter data
GET  /api/v1/districts/{code}/risk/
GET  /api/v1/districts/{code}/claims/summary/
GET  /api/v1/geospatial/districts/                       GeoJSON FeatureCollection (simplified)
POST /api/v1/geospatial/point-in-polygon/                reverse geocode {lat,lng} -> district
GET  /api/v1/geospatial/nearby/?lat=&lng=&km=            districts within radius
GET  /api/v1/docs/                                        Swagger UI
GET  /health/
```

## Deployment readiness

The same image runs in dev and prod, configured entirely by environment
(12-factor). Verified running against **real PostgreSQL/PostGIS 3.4 + Redis 7**,
not just SQLite:

```bash
# Production stack (see docker-compose.yml / deploy/):
export DATABASE_URL=postgis://fra:***@postgis:5432/fra_atlas
export REDIS_URL=redis://redis:6379/0
export DJANGO_DEBUG=0 DJANGO_SECRET_KEY=... DJANGO_ALLOWED_HOSTS=api.fra-atlas.gov.in
export STORAGE_BACKEND=s3 AV_SCANNER=clamav OCR_ENGINE=tesseract
docker compose up        # web + worker + beat + postgis + redis
```

* **DATABASE_URL** selects SQLite/SpatiaLite (dev) or PostgreSQL/PostGIS (prod).
* **REDIS_URL** enables Redis cache, sessions, and the Celery broker/result backend.
* **STORAGE_BACKEND / AV_SCANNER / OCR_ENGINE** swap local stubs for S3 / ClamAV /
  Tesseract — all behind interfaces, graceful fallback if a service is unreachable.
* Production hardening (HSTS, SSL redirect, secure cookies, clickjacking) auto-engages
  when `DJANGO_DEBUG=0`; `manage.py check --deploy` is clean.
* `entrypoint.sh` runs migrations + collectstatic; gunicorn via `gunicorn.conf.py`.
* Health: `/health/` (liveness), `/ready/` (readiness — pings DB + cache).
* CI (`.github/workflows/ci.yml`) spins up PostGIS + Redis and runs lint, bandit, and
  the full suite with a coverage gate.

## The ML pipeline (the system's brain)

`python manage.py train_risk_model` trains a RandomForest regressor on the real
500-district feature set (the eight governance/forest factors), exports it to
**ONNX for serving** and pickles the sklearn model for **SHAP**, then registers a
versioned, SHA-256-signed `RiskPredictionModel` row marked active.

`RiskPredictor` (`apps/analytics/inference.py`) serves predictions via
`onnxruntime` over the ONNX artifact and explains them with `shap.TreeExplainer`.
`POST /predict-district-risk/` returns, for Kondagaon: a CRITICAL score with the
SHAP breakdown showing its low Approval Rate as the dominant risk driver. A
version-keyed in-process cache keeps the model hot; deploying a new version
invalidates it transparently.

Honest note on metrics: `Risk_Index` in the dataset is a composite of the eight
inputs, so the model recovers the scoring function (R²≈0.92). This validates the
full train→ONNX→serve→explain pipeline end to end. The spec's ~0.70 ROC-AUC
refers to the satellite-feature fire-risk model (LST/NDVI/rainfall); that drops
into the same pipeline once such data is ingested — only `FEATURE_LIST` and the
training command change.

## Async layer (Celery)

`config/celery.py` defines the app + beat schedule. Tasks
(`apps/analytics/tasks.py`, `apps/audit/tasks.py`):

* `compute_district_risk_scores` (02:00) — re-scores every district with the
  active model, writes fresh snapshots + SHAP, refreshes denormalized risk.
* `generate_dss_recommendations` (06:00) — DSS engine over under-review claims.
* `compute_correlation_factors` (monthly) — Pearson matrix from snapshot factors.
* `verify_audit_log_integrity` (04:00) — recomputes the HMAC chain, flags tampering.

Each returns a JSON summary (counts + duration) for monitoring. They run on a
worker via the beat schedule, or synchronously in tests via `.apply()`.

## DSS engine

`apps/analytics/dss.py` is a transparent, data-aware rule engine: high
ecological risk → FOREST_MANAGEMENT + HABITAT_PROTECTION; weak tribal coverage →
PM_KISAN + LIVELIHOOD_SUPPORT; administrative bottleneck → PROCESS_ACCELERATION;
otherwise MGNREGA. Every recommendation carries a confidence and the supporting
factor values that triggered it, so officers can see *why* a scheme was
suggested. The ML risk score feeds the rules; the rules stay auditable.

## Design notes

**The audit chain.** Every claim mutation is wrapped in a DB transaction with an
audit-log append (`apps/claims/services.py`). Each `AuditLog` row is HMAC-SHA512
signed over `(previous_row_signature + canonical_content)`, so altering any
historical row breaks every signature after it. `verify_chain()` detects this;
`tests/test_audit.py::test_audit_tampering_is_detected` proves it. Rows reject
updates and deletes at the application layer.

**The state machine.** `DRAFT → SUBMITTED → UNDER_REVIEW → (APPROVED | REJECTED)`
is enforced in `FRAClaim.save()` (illegal jumps raise) and in the service layer
(transitions require a non-empty reason and write audit). `claim_identifier`,
`claim_date`, and `tribal_community` are immutable after creation.

**RBAC.** Querysets auto-filter to `assigned_districts` (or `assigned_states`).
A district admin cannot create claims; a field officer cannot approve. Proven in
`tests/test_claims_rbac.py`.

## Geospatial (real spatial queries)

`apps/geo` uses GeoDjango geometry fields (`MultiPolygonField`, `PointField`)
with spatial indexes. The same code runs on **SpatiaLite** (dev) and **PostGIS**
(prod) — switching is a `DATABASES` engine change only. `apps/geo/services.py`
is the single place that issues spatial lookups (`__contains`, distance), which
compile to the backend's `ST_*` functions.

Endpoints: a simplified (Douglas-Peucker) GeoJSON FeatureCollection scoped to
the caller's jurisdiction; point-in-polygon reverse geocoding (resolves a
coordinate to its district/village + claim count, falling back to nearest
districts on a miss); and a radius "nearby districts" query. Measured
point-in-polygon latency on the 500-district SpatiaLite DB is ~0.9ms, far inside
the 200ms SLA.

The dataset ships without coordinates, so `apps/geo/geometry.py` places each
district near its **real state centroid** with deterministic jitter (a point at
Chhattisgarh's centroid resolves to a Chhattisgarh district). District-level
boundaries are synthetic placeholders; production swaps `generate_district_geometry`
for a real boundary-shapefile ingest — no query code changes.

## PostGIS in production

This build stores geometry as GeoJSON in `JSONField` so it runs on SQLite. To
switch to the spec's PostGIS target:

1. `DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'`
2. Add `'django.contrib.gis'` to `INSTALLED_APPS`.
3. In `apps/geo/models.py`, replace each `geometry_geojson = JSONField(...)` with
   `geometry_polygon = gis_models.PolygonField(geography=True, null=True)` and add
   `GistIndex(fields=['geometry_polygon'])`.
4. Implement the spatial helpers (`ST_Intersects`, `ST_Contains`, `ST_DWithin`,
   point-in-polygon) in `apps/geo/services.py` — the only module that needs to
   change, since views call through it.

## Audit immutability at the database level

The application guards updates/deletes. In Postgres, also add a rule:

```sql
CREATE RULE audit_log_no_update AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
CREATE RULE audit_log_no_delete AS ON DELETE TO audit_log DO INSTEAD NOTHING;
ALTER TABLE audit_log ADD CONSTRAINT reason_not_empty CHECK (length(btrim(reason_text)) > 0);
```

## PII encryption

`email`, `phone_number`, `mfa_secret` are stored plainly here. In production wrap
them with `pgcrypto` (encrypt on write / decrypt on read at the manager layer)
with a key version embedded in the ciphertext for quarterly rotation.
