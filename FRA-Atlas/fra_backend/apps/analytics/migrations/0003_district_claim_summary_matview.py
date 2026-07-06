"""Materialized view for district claim summaries (spec Phase 4).

Postgres-only: created with a UNIQUE index so it can be refreshed with
REFRESH MATERIALIZED VIEW CONCURRENTLY (zero read-downtime). On SpatiaLite/dev
this is a no-op and the summary endpoint falls back to live ORM aggregation.
"""
from django.db import migrations

CREATE_SQL = """
CREATE MATERIALIZED VIEW IF NOT EXISTS district_claim_summary AS
SELECT
    d.id                AS district_id,
    d.district_code     AS district_code,
    d.name_english      AS name_english,
    COUNT(fc.id)                                          AS total_claims,
    COUNT(fc.id) FILTER (WHERE fc.status = 'APPROVED')    AS approved_claims,
    COUNT(fc.id) FILTER (WHERE fc.status = 'UNDER_REVIEW') AS pending_claims,
    COUNT(DISTINCT fc.tribal_community_id)                AS unique_communities
FROM geo_district d
LEFT JOIN fra_claim fc
       ON fc.district_id = d.id AND fc.soft_deleted_at IS NULL
WHERE d.soft_deleted_at IS NULL
GROUP BY d.id, d.district_code, d.name_english;

CREATE UNIQUE INDEX IF NOT EXISTS district_claim_summary_pk
    ON district_claim_summary (district_code);
"""

DROP_SQL = "DROP MATERIALIZED VIEW IF EXISTS district_claim_summary;"


def forwards(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(CREATE_SQL)


def backwards(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(DROP_SQL)


class Migration(migrations.Migration):
    dependencies = [
        ("analytics", "0001_initial"),
        ("claims", "0001_initial"),
        ("geo", "0001_initial"),
    ]
    operations = [migrations.RunPython(forwards, backwards)]
