# FRA Atlas Backend — Operations Runbook

## Deploy
1. Build & push image: `docker build -t fra-atlas:<tag> .`
2. `helm upgrade --install fra deploy/helm -f deploy/helm/values.yaml --set image.tag=<tag>`
   (or `kubectl apply -f deploy/k8s/`)
3. Run migrations: `kubectl exec deploy/fra-web -- python manage.py migrate`
4. Load/train (first deploy only): `load_fra_data` then `train_risk_model`.

## Scheduled jobs (Celery beat, UTC)
| Job | Schedule | SLA |
|-----|----------|-----|
| compute_district_risk_scores | 02:00 daily | 6h |
| generate_dss_recommendations | 06:00 daily | 2h |
| verify_audit_log_integrity | 04:00 daily | — |
| archive_and_snapshot_data | Sun 22:00 | — |
| sync_external_systems | hourly | — |
| compute_correlation_factors | 1st of month 03:00 | — |
| generate_performance_reports | Mon 08:00 | — |

## Incident: audit tampering alert
`verify_audit_log_integrity` returns `TAMPERING_DETECTED` with broken row IDs.
Treat as a security incident: freeze writes, snapshot the DB, escalate. Do not
delete or "fix" rows — the break itself is evidence.

## Incident: DLQ growth
Failed tasks land in `ops_dead_letter`. Inspect `error_message`, fix the cause,
re-enqueue manually. After 3 consecutive external-sync failures, auto-sync
disables itself (`ExternalSystemIntegration.auto_sync_enabled=False`) — re-enable
once the upstream is healthy.

## Key rotation (quarterly)
Audit signing key (`AUDIT_LOG_SECRET`) and PII encryption keys
(`ENCRYPTION_KEYS`): add the new key, bump `ENCRYPTION_ACTIVE_VERSION`, keep old
keys for historical decryption/verification. Never remove an old key while rows
signed/encrypted with it remain.

## RTO/RPO
RTO < 1h (redeploy + restore latest snapshot). RPO < 15min (streaming replica) /
nightly snapshot for cold restore.
