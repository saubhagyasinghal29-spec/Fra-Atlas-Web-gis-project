"""Reusable base models enforcing the spec's cross-cutting data rules:

* UUID primary keys (no sequential IDs that leak business intelligence)
* timezone-aware created_at / updated_at (UTC storage)
* soft-delete semantics (soft_deleted_at) -- hard delete never occurs
"""
import uuid

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(soft_deleted_at__isnull=True)

    def dead(self):
        return self.filter(soft_deleted_at__isnull=False)

    def delete(self):
        # Soft-delete in bulk; never issues a SQL DELETE.
        return self.update(soft_deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class BaseModel(models.Model):
    """UUID PK + audit timestamps + soft delete. Inherited by every entity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    soft_deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft delete. Use hard_delete() only in data-retention jobs."""
        self.soft_deleted_at = timezone.now()
        self.save(update_fields=["soft_deleted_at", "updated_at"])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)
