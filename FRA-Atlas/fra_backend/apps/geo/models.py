"""District / Village / TribalCommunity with real GeoDjango geometry.

Geometry columns are PostGIS/SpatiaLite geometry fields with spatial indexes.
The same model code runs on SpatiaLite (dev) and PostGIS (prod) -- GeoDjango
abstracts the backend, so switching is a settings.DATABASES change only.

All spatial *queries* live in apps/geo/services.py so views never touch the ORM
spatial lookups directly.
"""
from django.contrib.gis.db import models as gis
from django.db import models

from apps.common.enums import RiskCategory
from apps.common.models import BaseModel


class District(BaseModel):
    district_code = models.CharField(max_length=16, unique=True, db_index=True)
    name_english = models.CharField(max_length=128)
    state = models.CharField(max_length=64, db_index=True)
    tribal_population = models.PositiveIntegerField(default=0)
    geometry = gis.MultiPolygonField(srid=4326, null=True, blank=True, spatial_index=True)
    centroid = gis.PointField(srid=4326, null=True, blank=True, spatial_index=True)

    risk_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    risk_category = models.CharField(
        max_length=16, choices=RiskCategory.choices, null=True, blank=True
    )
    last_risk_update_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "geo_district"
        indexes = [models.Index(fields=["state", "district_code"])]

    def __str__(self):
        return f"{self.name_english} ({self.district_code})"


class TribalCommunity(BaseModel):
    name_english = models.CharField(max_length=128)
    district = models.ForeignKey(
        District, on_delete=models.PROTECT, related_name="communities"
    )
    territory = gis.MultiPolygonField(srid=4326, null=True, blank=True, spatial_index=True)
    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "geo_tribal_community"

    @property
    def district_code(self):
        return self.district.district_code

    @property
    def state(self):
        return self.district.state


class Village(BaseModel):
    village_code = models.CharField(max_length=24, unique=True, db_index=True)
    village_name = models.CharField(max_length=128)
    district = models.ForeignKey(
        District, on_delete=models.PROTECT, related_name="villages"
    )
    geometry = gis.PolygonField(srid=4326, null=True, blank=True, spatial_index=True)
    location = gis.PointField(srid=4326, null=True, blank=True, spatial_index=True)
    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "geo_village"

    @property
    def district_code(self):
        return self.district.district_code

    @property
    def state(self):
        return self.district.state
