"""Report generation worker. Builds CSV/XLSX from claim/district data, stores
it, and tracks progress on the ReportJob row."""
import csv
import io
import time

from celery import shared_task
from django.utils import timezone

from apps.documents.services import get_storage
from apps.reports.models import ReportJob, ReportStatus


def _rows_for(report_type, filters):
    from apps.claims.models import FRAClaim
    from apps.geo.models import District

    if report_type == "risk_ranking":
        header = ["district_code", "name", "state", "risk_score", "risk_category"]
        qs = District.objects.exclude(risk_score__isnull=True).order_by("-risk_score")
        rows = [[d.district_code, d.name_english, d.state,
                 float(d.risk_score), d.risk_category] for d in qs]
        return header, rows

    # default: district_claims
    header = ["claim_identifier", "district_code", "status", "claim_type",
              "area_hectares", "claim_date"]
    qs = FRAClaim.objects.select_related("district").all()
    if filters.get("status"):
        qs = qs.filter(status=filters["status"])
    if filters.get("district_code"):
        qs = qs.filter(district__district_code=filters["district_code"])
    rows = [[c.claim_identifier, c.district_code, c.status, c.claim_type,
             str(c.area_hectares), str(c.claim_date)] for c in qs]
    return header, rows


def _serialize(header, rows, fmt):
    if fmt == "XLSX":
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "report"
        ws.append(header)
        for r in rows:
            ws.append(r)
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue(), "xlsx"
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue().encode(), "csv"


@shared_task(bind=True, max_retries=2)
def generate_report(self, job_id):
    started = time.monotonic()
    job = ReportJob.objects.get(id=job_id)
    job.status = ReportStatus.RUNNING
    job.progress_percent = 10
    job.save(update_fields=["status", "progress_percent", "updated_at"])
    try:
        header, rows = _rows_for(job.report_type, job.filters_json or {})
        job.progress_percent = 60
        job.save(update_fields=["progress_percent"])
        content, ext = _serialize(header, rows, job.export_format)
        key = f"reports/{job.id}.{ext}"
        get_storage().save(key, content)
        job.storage_key = key
        job.status = ReportStatus.COMPLETE
        job.progress_percent = 100
        job.expires_at = timezone.now() + timezone.timedelta(days=7)
        job.save(update_fields=["storage_key", "status", "progress_percent",
                                "expires_at", "updated_at"])
    except Exception as exc:  # noqa
        job.status = ReportStatus.FAILED
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message", "updated_at"])
        raise
    return {"status": "ok", "job_id": str(job.id), "rows": len(rows),
            "duration_s": round(time.monotonic() - started, 2)}
