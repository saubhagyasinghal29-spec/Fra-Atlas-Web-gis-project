"""FRA claim domain with an enforced finite-state machine.

State graph:  DRAFT -> SUBMITTED -> UNDER_REVIEW -> (APPROVED | REJECTED)

* Immutable fields (claim_date, claim_identifier, tribal_community) cannot be
  changed after creation -- enforced in save().
* status changes are only legal along VALID_TRANSITIONS -- enforced in save();
  every transition appends a timestamped entry to status_history.
Business operations (submit/review/approve/reject) go through services.py so
each transition also writes an audit-chain entry atomically.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.common.enums import ClaimStatus, ClaimType
from apps.common.models import BaseModel
from apps.geo.models import District, TribalCommunity, Village

IMMUTABLE_FIELDS = ("claim_identifier", "claim_date", "tribal_community_id")

VALID_TRANSITIONS = {
    ClaimStatus.DRAFT: {ClaimStatus.SUBMITTED},
    ClaimStatus.SUBMITTED: {ClaimStatus.UNDER_REVIEW},
    ClaimStatus.UNDER_REVIEW: {ClaimStatus.APPROVED, ClaimStatus.REJECTED},
    ClaimStatus.APPROVED: set(),
    ClaimStatus.REJECTED: set(),
}


class FRAClaim(BaseModel):
    claim_identifier = models.CharField(max_length=32, unique=True, db_index=True)
    claim_type = models.CharField(max_length=8, choices=ClaimType.choices)
    status = models.CharField(
        max_length=16, choices=ClaimStatus.choices,
        default=ClaimStatus.DRAFT, db_index=True,
    )
    tribal_community = models.ForeignKey(
        TribalCommunity, on_delete=models.PROTECT, related_name="claims"
    )
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="claims")
    village = models.ForeignKey(
        Village, on_delete=models.PROTECT, related_name="claims", null=True, blank=True
    )
    area_hectares = models.DecimalField(max_digits=12, decimal_places=2,
                                        default=Decimal("0.00"))
    claim_date = models.DateField()
    forest_location_geojson = models.JSONField(null=True, blank=True)
    status_history = models.JSONField(default=list, blank=True)
    dss_recommendations_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "fra_claim"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["district", "status"]),
            models.Index(fields=["tribal_community", "status"]),
        ]

    # -- spec helpers -------------------------------------------------------
    @property
    def district_code(self):
        return self.district.district_code

    @property
    def state(self):
        return self.district.state

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        # remember persisted values to detect illegal mutations on save
        instance._loaded = dict(zip(field_names, values, strict=False))
        return instance

    def clean(self):
        if self.area_hectares is not None and self.area_hectares <= 0:
            raise ValidationError({"area_hectares": "Must be > 0"})

    def save(self, *args, **kwargs):
        if not self._state.adding and getattr(self, "_loaded", None):
            for field in IMMUTABLE_FIELDS:
                if self._loaded.get(field) != getattr(self, field):
                    raise ValidationError(
                        {field: f"'{field}' is immutable and cannot be modified."}
                    )
            old_status = self._loaded.get("status")
            if old_status != self.status:
                allowed = VALID_TRANSITIONS.get(old_status, set())
                if self.status not in allowed:
                    raise ValidationError(
                        {"status": f"Illegal transition {old_status} -> {self.status}"}
                    )
        super().save(*args, **kwargs)
        self._loaded = {f: getattr(self, f) for f in
                        ("claim_identifier", "claim_date", "tribal_community_id", "status")}

    def can_transition_to(self, target):
        return target in VALID_TRANSITIONS.get(self.status, set())


class DSSRecommendation(BaseModel):
    fra_claim = models.ForeignKey(
        FRAClaim, on_delete=models.PROTECT, related_name="dss_recommendations"
    )
    recommendation_type = models.CharField(max_length=32)  # MGNREGA, PM_KISAN, ...
    confidence_score = models.DecimalField(max_digits=4, decimal_places=3, default=0)
    supporting_factors = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "dss_recommendation"
