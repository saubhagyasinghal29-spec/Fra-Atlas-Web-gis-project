"""Asynchronous report jobs."""
from django.db import models

from apps.common.models import BaseModel


class ReportStatus(models.TextChoices):
    QUEUED = "QUEUED", "Queued"
    RUNNING = "RUNNING", "Running"
    COMPLETE = "COMPLETE", "Complete"
    FAILED = "FAILED", "Failed"


class ReportJob(BaseModel):
    report_type = models.CharField(max_length=40)  # e.g. district_claims, risk_ranking
    export_format = models.CharField(max_length=8, default="CSV")  # CSV | XLSX
    status = models.CharField(max_length=10, choices=ReportStatus.choices,
                              default=ReportStatus.QUEUED)
    progress_percent = models.PositiveSmallIntegerField(default=0)
    filters_json = models.JSONField(default=dict, blank=True)
    storage_key = models.CharField(max_length=512, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    requested_by = models.UUIDField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "report_job"
