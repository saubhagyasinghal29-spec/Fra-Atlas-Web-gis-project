import datetime
from decimal import Decimal
from io import BytesIO

import pytest

from apps.common.enums import ClaimStatus

pytestmark = pytest.mark.django_db


def _claim(field_officer, district, community):
    from apps.claims import services
    return services.create_claim(
        actor=field_officer, district=district, tribal_community=community,
        claim_type="CFR", area_hectares=Decimal("10"), claim_date=datetime.date(2024, 1, 1),
    )


def _png_bytes():
    return b"\x89PNG\r\n\x1a\n" + b"0" * 64


# ---------------------------------------------------------- documents --------
def test_document_upload_and_list(admin_api, field_officer, district, community):
    from django.core.files.uploadedfile import SimpleUploadedFile
    claim = _claim(field_officer, district, community)
    f = SimpleUploadedFile("survey.png", _png_bytes(), content_type="image/png")
    resp = admin_api.post(f"/api/v1/fra-claims/{claim.id}/documents/", {"file": f},
                          format="multipart")
    assert resp.status_code == 201
    assert resp.data["scan_status"] == "CLEAN" and resp.data["filename"] == "survey.png"
    listed = admin_api.get(f"/api/v1/fra-claims/{claim.id}/documents/")
    assert len(listed.data) == 1


def test_document_rejects_bad_type(admin_api, field_officer, district, community):
    from django.core.files.uploadedfile import SimpleUploadedFile
    claim = _claim(field_officer, district, community)
    f = SimpleUploadedFile("x.exe", b"MZ", content_type="application/x-msdownload")
    resp = admin_api.post(f"/api/v1/fra-claims/{claim.id}/documents/", {"file": f},
                          format="multipart")
    assert resp.status_code == 415


def test_document_rejects_malware(admin_api, field_officer, district, community):
    from django.core.files.uploadedfile import SimpleUploadedFile
    claim = _claim(field_officer, district, community)
    eicar = b"%PDF-1.4 X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    f = SimpleUploadedFile("v.pdf", eicar, content_type="application/pdf")
    resp = admin_api.post(f"/api/v1/fra-claims/{claim.id}/documents/", {"file": f},
                          format="multipart")
    assert resp.status_code == 422


# ------------------------------------------------------------ reports --------
def test_report_generation_task(db, admin_api):
    from apps.reports.models import ReportJob, ReportStatus
    from apps.reports.tasks import generate_report
    job = ReportJob.objects.create(report_type="district_claims", export_format="CSV")
    generate_report.apply(args=[str(job.id)])
    job.refresh_from_db()
    assert job.status == ReportStatus.COMPLETE
    assert job.storage_key.endswith(".csv") and job.progress_percent == 100


def test_report_generate_endpoint_requires_analytics_perm(admin_api, api):
    # admin has VIEW_ANALYTICS, field officer (api) does not
    ok = admin_api.post("/api/v1/reports/generate/",
                        {"report_type": "risk_ranking", "export_format": "CSV"}, format="json")
    assert ok.status_code == 202 and "job_id" in ok.data
    forbidden = api.post("/api/v1/reports/generate/",
                         {"report_type": "risk_ranking"}, format="json")
    assert forbidden.status_code == 403


# -------------------------------------------------------------- ops ----------
def test_snapshot_task_writes_record(db):
    from apps.ops.models import BatchJob, DataSnapshot
    from apps.ops.tasks import archive_and_snapshot_data
    result = archive_and_snapshot_data.apply().get()
    assert result["status"] == "ok"
    assert DataSnapshot.objects.count() == 1
    assert BatchJob.objects.filter(task_name="archive_and_snapshot_data",
                                   status="SUCCESS").exists()


def test_external_sync_task(db):
    from apps.ops.models import ExternalSystemIntegration
    from apps.ops.tasks import sync_external_systems
    assert sync_external_systems.apply().get()["status"] == "ok"
    assert ExternalSystemIntegration.objects.count() == 3


def test_performance_report_task(db):
    from apps.ops.tasks import generate_performance_reports
    result = generate_performance_reports.apply().get()
    assert result["status"] == "ok" and "approval_rate_pct" in result


def test_dead_letter_on_failure(db):
    """A task that raises past its retries lands in the DLQ via LoggedTask."""
    from celery import shared_task
    from apps.ops.models import DeadLetterTask
    from apps.ops.tasks import LoggedTask

    @shared_task(base=LoggedTask, bind=True, name="tests.always_fails")
    def always_fails(self):
        raise RuntimeError("boom")

    res = always_fails.apply()
    assert res.failed()
    assert DeadLetterTask.objects.filter(task_name="tests.always_fails").exists()
