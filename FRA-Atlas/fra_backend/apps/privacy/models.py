"""DPDP Act 2023 data-subject request records."""
from django.db import models

from apps.common.models import BaseModel


class DataSubjectRequest(BaseModel):
    class Type(models.TextChoices):
        ACCESS = "ACCESS", "Access / portability"
        ERASURE = "ERASURE", "Erasure"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        REJECTED = "REJECTED", "Rejected"

    subject_user_id = models.UUIDField()
    request_type = models.CharField(max_length=10, choices=Type.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    completed_at = models.DateTimeField(null=True, blank=True)
    result_json = models.JSONField(default=dict, blank=True)
    legal_basis_note = models.TextField(blank=True, default="")

    class Meta:
        db_table = "privacy_data_subject_request"
