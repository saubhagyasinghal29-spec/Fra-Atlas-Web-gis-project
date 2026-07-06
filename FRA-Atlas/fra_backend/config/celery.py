"""Celery application + beat schedule for the FRA Atlas backend.

Broker/result-backend default to Redis/DB per the spec; override via env. Tasks
are written so they can also be invoked synchronously with `.apply()` (used by
the test suite) without a running broker.
"""
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("fra_atlas")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Spec's scheduled jobs (UTC).
app.conf.beat_schedule = {
    "nightly-risk-recompute": {
        "task": "apps.analytics.tasks.compute_district_risk_scores",
        "schedule": crontab(hour=2, minute=0),
    },
    "daily-dss-generation": {
        "task": "apps.analytics.tasks.generate_dss_recommendations",
        "schedule": crontab(hour=6, minute=0),
    },
    "monthly-correlation": {
        "task": "apps.analytics.tasks.compute_correlation_factors",
        "schedule": crontab(day_of_month=1, hour=3, minute=0),
    },
    "daily-audit-verification": {
        "task": "apps.audit.tasks.verify_audit_log_integrity",
        "schedule": crontab(hour=4, minute=0),
    },
    "weekly-data-snapshot": {
        "task": "apps.ops.tasks.archive_and_snapshot_data",
        "schedule": crontab(day_of_week="sun", hour=22, minute=0),
    },
    "hourly-external-sync": {
        "task": "apps.ops.tasks.sync_external_systems",
        "schedule": crontab(minute=0),
    },
    "weekly-performance-report": {
        "task": "apps.ops.tasks.generate_performance_reports",
        "schedule": crontab(day_of_week="mon", hour=8, minute=0),
    },
    "nightly-matview-refresh": {
        "task": "apps.analytics.tasks.refresh_materialized_views",
        "schedule": crontab(hour=1, minute=30),
    },
    "daily-drift-monitor": {
        "task": "apps.analytics.tasks.monitor_prediction_drift",
        "schedule": crontab(hour=5, minute=0),
    },
    "yearly-retention-enforce": {
        "task": "apps.ops.tasks.enforce_retention",
        "schedule": crontab(day_of_month=1, month_of_year=4, hour=0, minute=0),
    },
}
