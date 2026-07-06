"""Materialized-view helpers (Postgres). Callers fall back to ORM elsewhere."""
from django.db import connection

MATVIEWS = ["district_claim_summary"]


def is_postgres():
    return connection.vendor == "postgresql"


def refresh_all(concurrently=True):
    if not is_postgres():
        return {"refreshed": [], "skipped": "not postgres"}
    refreshed = []
    with connection.cursor() as cur:
        for mv in MATVIEWS:
            mode = "CONCURRENTLY " if concurrently else ""
            try:
                cur.execute(f"REFRESH MATERIALIZED VIEW {mode}{mv}")
            except Exception:
                cur.execute(f"REFRESH MATERIALIZED VIEW {mv}")  # first refresh can't be concurrent
            refreshed.append(mv)
    return {"refreshed": refreshed}


def district_summary_row(district_code):
    """Read a single district's summary from the matview. Returns dict or None."""
    if not is_postgres():
        return None
    with connection.cursor() as cur:
        cur.execute(
            "SELECT total_claims, approved_claims, pending_claims, unique_communities "
            "FROM district_claim_summary WHERE district_code = %s", [district_code])
        row = cur.fetchone()
    if not row:
        return None
    return {"total_claims": row[0], "approved_claims": row[1],
            "pending_claims": row[2], "unique_communities": row[3]}
