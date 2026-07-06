"""Fixed value sets used across the domain (stored as CharField choices).

Postgres ENUM types are the production target; Django's TextChoices give the
same application-layer guarantees and are portable to SQLite for this build.
"""
from django.db import models


class ClaimStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    UNDER_REVIEW = "UNDER_REVIEW", "Under review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class ClaimType(models.TextChoices):
    INDIVIDUAL_FOREST = "IFR", "Individual Forest Right"
    COMMUNITY_FOREST = "CFR", "Community Forest Right"
    COMMUNITY_RESOURCE = "CR", "Community Resource Right"


class RiskCategory(models.TextChoices):
    LOW = "LOW", "Low"
    MODERATE = "MODERATE", "Moderate"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class Designation(models.TextChoices):
    FIELD_OFFICER = "FIELD_OFFICER", "Field Officer"
    BLOCK_OFFICIAL = "BLOCK_OFFICIAL", "Block Official"
    DISTRICT_ADMIN = "DISTRICT_ADMIN", "District Administrator"
    STATE_COORDINATOR = "STATE_COORDINATOR", "State Coordinator"
    ML_RESEARCHER = "ML_RESEARCHER", "ML Researcher"
    SUPERUSER = "SUPERUSER", "Superuser"
    ML_SYSTEM = "ML_SYSTEM", "ML System (automated)"


class AuditAction(models.TextChoices):
    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    DELETE = "DELETE", "Delete"
    TRANSITION = "TRANSITION", "State transition"
    APPROVE = "APPROVE", "Approve"
    REJECT = "REJECT", "Reject"


class Permission(models.TextChoices):
    VIEW_CLAIM = "VIEW_CLAIM", "View claim"
    CREATE_CLAIM = "CREATE_CLAIM", "Create claim"
    EDIT_CLAIM = "EDIT_CLAIM", "Edit claim"
    SUBMIT_CLAIM = "SUBMIT_CLAIM", "Submit claim"
    REVIEW_CLAIM = "REVIEW_CLAIM", "Move claim to review"
    APPROVE_CLAIM = "APPROVE_CLAIM", "Approve claim"
    REJECT_CLAIM = "REJECT_CLAIM", "Reject claim"
    VIEW_ANALYTICS = "VIEW_ANALYTICS", "View analytics"
