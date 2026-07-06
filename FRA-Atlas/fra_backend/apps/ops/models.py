"""Operational records: batch-job logs, data snapshots, external-system sync,
and a dead-letter queue for tasks that exhaust their retries."""
from django.db import models

from apps.common.models import BaseModel


class BatchJob(BaseModel):
    task_name = models.CharField(max_length=120, db_index=True)
    status = models.CharField(max_length=16, default="RUNNING")  # RUNNING|SUCCESS|FAILED
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_s = models.FloatField(null=True, blank=True)
    record_count = models.IntegerField(default=0)
    result_json = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        db_table = "ops_batch_job"
        indexes = [models.Index(fields=["task_name", "created_at"])]


class DataSnapshot(BaseModel):
    content_hash = models.CharField(max_length=64)
    row_counts_json = models.JSONField(default=dict)
    storage_key = models.CharField(max_length=512, blank=True, default="")
    verified = models.BooleanField(default=False)

    class Meta:
        db_table = "ops_data_snapshot"


class ExternalSystemIntegration(BaseModel):
    system_name = models.CharField(max_length=80)  # ForestDept, Census, WildlifeBoard
    last_sync_at = models.DateTimeField(null=True, blank=True)
    records_synced_count = models.IntegerField(default=0)
    consecutive_failures = models.PositiveIntegerField(default=0)
    auto_sync_enabled = models.BooleanField(default=True)
    error_message_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ops_external_integration"


class DeadLetterTask(BaseModel):
    task_name = models.CharField(max_length=120)
    args_json = models.JSONField(default=list)
    kwargs_json = models.JSONField(default=dict)
    error_message = models.TextField()
    retries = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "ops_dead_letter"
