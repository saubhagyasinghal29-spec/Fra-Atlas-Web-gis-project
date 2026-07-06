"""Claim document attachments with malware-scan + OCR metadata."""
from django.db import models

from apps.claims.models import FRAClaim
from apps.common.models import BaseModel

ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


class ScanStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CLEAN = "CLEAN", "Clean"
    INFECTED = "INFECTED", "Infected"
    ERROR = "ERROR", "Error"


class Attachment(BaseModel):
    fra_claim = models.ForeignKey(FRAClaim, on_delete=models.PROTECT,
                                  related_name="attachments")
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size_bytes = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64, db_index=True)
    storage_key = models.CharField(max_length=512)
    scan_status = models.CharField(max_length=10, choices=ScanStatus.choices,
                                   default=ScanStatus.PENDING)
    ocr_text = models.TextField(blank=True, default="")
    uploaded_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "document_attachment"
        indexes = [models.Index(fields=["fra_claim", "created_at"])]
