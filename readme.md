# National FRA Atlas
### Forest Rights Act Decision Support System — Ministry of Tribal Affairs
 
A full-stack platform for administering Forest Rights Act (FRA, 2006) claims,
scoring district-level implementation risk with machine learning, and
recommending welfare-scheme interventions — built as Django/DRF + PostgreSQL/PostGIS
on the backend and a React 19 + Vite portal on the frontend.
 
---
 
## 1. What this system does
 
**Claims administration**
- Digitizes the FRA claim lifecycle: `DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED/REJECTED`,
  with immutable fields once a claim leaves draft state.
- Every state change, edit, and access is written to an **immutable, HMAC-SHA512
  chained audit log** — tamper-evident by design, verifiable with a built-in checker.
- Role-based access (6 roles) with **geographic scoping** — a state coordinator only
  sees their assigned states/districts.
**Spatial data**
- GeoDjango-backed district boundaries; point-in-polygon claim mapping
  (e.g. resolving a GPS coordinate to its district) via `ST_Contains`.
- Runs on SpatiaLite in dev and PostGIS in production from the same codebase.
**Risk intelligence (ML)**
- A RandomForest model (exported to ONNX, explained with SHAP) scores every
  district on FRA-implementation risk from 8 governance factors: approval rate,
  pending-claims rate, average processing time, forest-loss rate, tribal
  population coverage, CFR recognition rate, rejection rate, and encroachment
  density.
- Districts are ranked and clustered (PCA + K-Means) into a 4-tier scheme:
  **Critical / Moderate / Good / Excellent**.
- Drift monitoring (PSI) and a fairness report are built in for ongoing model
  governance, with a human-in-the-loop invariant enforced by tests.
**Decision Support (DSS)**
- A rule engine turns a district's risk factors into advisory welfare-scheme
  recommendations for on-the-ground follow-up.
**Portal (frontend)**
- **Dashboard** — headline risk counts and top-risk districts.
- **Map** — interactive Leaflet view of all districts, color-coded by risk tier.
- **Analytics** — correlation heatmap, PCA cluster plot, and top-50 risk ranking,
  generated from live model output.
- **DSS** — the recommendation engine, browsable per district.
- **Fire Forecast / Crop Recommender** — auxiliary ML-backed advisory tools.
- **Reports** — report generation UI.
- Gated behind JWT login; falls back to a bundled reference dataset if the API
  is unreachable, so the UI is never blank.
**Compliance & operations**
- DPDP Act (2023) data-subject rights: access export and crypto-erasure,
  reconciled against the immutable audit trail; documented retention policy.
- Real, verified backups (serialize → store → read-back → hash-verify) with
  `backup`/`restore` management commands.
- Offline mobile sync: delta pull/push with conflict tracking, for field use
  in low-connectivity areas.
- JWT token revocation (blacklist + rotation), MFA/TOTP, account lockout,
  magic-byte upload sniffing, and rate-limited APIs.
- Prometheus metrics + Grafana, health/readiness probes, CI with blocking
  lint/security scans and an enforced coverage gate.
---
 
## 2. Architecture
 
```
                        ┌────────────────────┐
   Browser  ──HTTP──►   │   React 19 + Vite   │   (localhost:5173)
   (JWT in                portal (this repo:   
   localStorage)          fra_frontend)        
                        └─────────┬──────────┘
                                  │ fetch() over HTTP, CORS-enabled
                                  ▼
                        ┌────────────────────┐
                        │  Django 5 + DRF     │   (localhost:8000)
                        │  fra_backend        │
                        └─────────┬──────────┘
                     ┌────────────┼────────────┐
                     ▼            ▼            ▼
              PostgreSQL/     Redis        Celery worker
              PostGIS         (cache,      + beat
              (claims,        sessions,    (scheduled
              districts,      Celery       jobs, drift
              audit log,      broker)      monitoring)
              ML snapshots)
```
 
The frontend and backend are independent processes communicating only over
HTTP on `localhost`. The frontend has no server-side logic of its own — it's a
static bundle served by Vite (or any static host in production) that calls the
Django API directly from the browser.
 
---
 
## 3. Tech stack
 
| Layer | Technology |
|---|---|
| Backend framework | Django 5, Django REST Framework |
| Database | PostgreSQL 16 + PostGIS 3.4 (prod), SpatiaLite (dev) |
| Cache / broker | Redis 7 |
| Background jobs | Celery (worker + beat) |
| ML | scikit-learn → ONNX, SHAP |
| Frontend framework | React 19.2, Vite 8, React Router 7 |
| Maps | react-leaflet 5 + leaflet.markercluster |
| Charts | Recharts 3 |
| Auth | JWT (access + refresh, rotation, blacklist) |
| Infra | Docker Compose, Kubernetes/Helm, GitHub Actions CI |
| Observability | Prometheus, Grafana, structured health/readiness endpoints |
 
---
 
## 4. Running it locally (Docker — recommended)
 
You need Docker Desktop installed and running, plus Node.js 20+ for the frontend.
 
### Backend
 
```bash
cd fra_backend
 
# 1. Start the database on its own first and let it fully initialize
docker compose up -d db
sleep 25
 
# 2. Run migrations once, in a single throwaway container.
#    (Do not skip this — starting all services at once on a brand-new
#    database causes web/worker/beat to race the migration step.)
docker compose run --rm web python manage.py migrate
 
# 3. Bring up the full stack
docker compose up -d
 
# 4. Load the reference dataset, train the risk model, seed a demo user
docker compose exec web python manage.py load_fra_data
docker compose exec web python manage.py train_risk_model
docker compose exec web python manage.py seed_demo_user
```
 
Before step 3, confirm `docker-compose.yml` has `DJANGO_DEBUG: "1"` for local
use — with `DEBUG=0` the app enables `SECURE_SSL_REDIRECT`, which 301-redirects
every plain-HTTP request (including the frontend's login call) and nothing
will work on `localhost` without HTTPS.
 
Verify it's healthy:
```bash
curl http://localhost:8000/health/     # liveness
curl http://localhost:8000/ready/      # DB + cache readiness
```
API docs: `http://localhost:8000/api/v1/docs/`
 
**If you hit `MigrationSchemaMissing` / duplicate-key errors on `web`:** the
Postgres volume is in a half-initialized state (usually from a previous
crashed run). Reset it and repeat the sequence above:
```bash
docker compose down -v
docker compose up -d db
sleep 25
docker compose run --rm web python manage.py migrate
docker compose up -d
```
 
### Frontend
 
```bash
cd fra_frontend
npm install
npm run dev
```
Open `http://localhost:5173`. Sign in with:
 
> **Username:** `analyst`
> **Password:** `FraAtlas@2026`
 
The `.env` file already points `VITE_API_BASE` at `http://localhost:8000`;
edit it if your backend runs elsewhere.
 
For a production-style build instead of the dev server:
```bash
npm run build && npm run preview
```
 
---
 
## 5. Verifying the system is working end-to-end
 
1. `http://localhost:8000/health/` returns `200 OK`.
2. Logging into the portal succeeds and the Dashboard shows **500 districts**
   with a live Critical/Moderate/Good/Excellent breakdown (no orange
   "bundled reference data" banner — that banner means the frontend couldn't
   reach the API).
3. The Map page plots all districts colour-coded by risk tier.
4. Analytics shows the correlation heatmap, PCA cluster plot, and top-50 risk
   ranking — all rendered from the trained model's real output.
5. `docker compose exec web python manage.py check --deploy` reports 0
   security warnings when `DEBUG=0` is used for an actual production deploy.
---
 
## 6. Known local-dev gotchas (already fixed in this build, kept here for reference)
 
- **All-services migrate race** — `web`, `worker`, and `beat` share an
  entrypoint that runs `migrate` on boot. On a brand-new database they can
  race and corrupt the migrations table. Always run `migrate` once via
  `docker compose run --rm web python manage.py migrate` before `up -d`.
- **HTTPS redirect on localhost** — `DEBUG=0` turns on `SECURE_SSL_REDIRECT`.
  Use `DJANGO_DEBUG=1` for local/demo use; only disable it behind a real
  TLS-terminating proxy in production.
- **CORS** — the frontend origin must be listed in `CORS_ALLOWED_ORIGINS` on
  the backend. `http://localhost:5173` is allowed by default.
---
 
## 7. Project status
 
Backend is deployment-ready and audit-remediated (backups, DPDP rights,
CI gating, token revocation, ML governance all closed against a stakeholder
audit). Frontend is a First Build: live-integrated with authentication, real
data, and real analytics outputs. Remaining known gaps: a full WCAG
accessibility audit and complete Hindi localization (toggle exists, full
translation pending), live external system integrations, and real (rather
than illustrative) district boundary shapefiles for the map.