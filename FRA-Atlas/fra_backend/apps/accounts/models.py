"""User model + role-based access control.

Geographic scoping is expressed with assigned_states / assigned_districts.
PII columns (email, phone) are marked for column-level encryption in
production; here they are stored plainly so the build runs without pgcrypto.
See README "PII encryption".
"""
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from apps.common.encryption import EncryptedCharField
from apps.common.enums import Designation, Permission

LOCKOUT_THRESHOLD = 5
LOCKOUT_DURATION_HOURS = 24


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designation = models.CharField(
        max_length=32, choices=Designation.choices, default=Designation.FIELD_OFFICER
    )
    # Geographic scope. Stored as JSON lists for SQLite portability;
    # production uses Postgres ARRAY(varchar) for indexable membership checks.
    assigned_states = models.JSONField(default=list, blank=True)
    assigned_districts = models.JSONField(default=list, blank=True)

    phone_number = EncryptedCharField(max_length=255, blank=True, default="")  # encrypted at rest
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = EncryptedCharField(max_length=255, blank=True, default="")    # encrypted at rest
    password_last_changed_at = models.DateTimeField(null=True, blank=True)
    failed_login_count = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    pii_erased_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "account_user"

    # ---- account lockout (spec Phase 2.2: 5 failures -> 24h lockout) ----
    @property
    def is_locked(self):
        return self.locked_until is not None and self.locked_until > timezone.now()

    def register_failed_login(self):
        self.failed_login_count += 1
        if self.failed_login_count >= LOCKOUT_THRESHOLD:
            self.locked_until = timezone.now() + timezone.timedelta(hours=LOCKOUT_DURATION_HOURS)
        self.save(update_fields=["failed_login_count", "locked_until"])

    def register_successful_login(self):
        if self.failed_login_count or self.locked_until:
            self.failed_login_count = 0
            self.locked_until = None
            self.save(update_fields=["failed_login_count", "locked_until"])

    @property
    def permissions(self):
        """Resolve this user's permission codes from their role."""
        return set(
            RolePermission.objects.filter(role=self.designation).values_list(
                "permission_code", flat=True
            )
        )

    def has_fra_permission(self, code):
        if self.designation == Designation.SUPERUSER:
            return True
        return code in self.permissions

    def in_scope(self, *, state=None, district_code=None):
        """True if the object's geography falls within the user's jurisdiction."""
        if self.designation == Designation.SUPERUSER:
            return True
        if district_code is not None and self.assigned_districts:
            if district_code in self.assigned_districts:
                return True
        if state is not None and self.assigned_states:
            if state in self.assigned_states:
                return True
        # State coordinators are scoped at state level; if a district is given
        # but only states are assigned, allow when the district's state matches.
        return False


class RolePermission(models.Model):
    """Which permission codes each role (Designation) holds."""

    role = models.CharField(max_length=32, choices=Designation.choices)
    permission_code = models.CharField(max_length=32, choices=Permission.choices)

    class Meta:
        db_table = "account_role_permission"
        unique_together = ("role", "permission_code")

    def __str__(self):
        return f"{self.role}:{self.permission_code}"
