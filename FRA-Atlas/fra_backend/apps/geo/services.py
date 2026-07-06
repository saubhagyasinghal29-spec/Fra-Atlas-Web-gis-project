"""Spatial query helpers. The ONLY module that issues GeoDjango spatial
lookups -- views call through here. Identical on SpatiaLite (dev) and
PostGIS (prod); the lookups (__contains, __dwithin, __distance) compile to the
backend's ST_* functions and use the spatial index.
"""
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from apps.geo.models import District, Village


def make_point(latitude: float, longitude: float) -> Point:
    # GIS convention: Point(x=lon, y=lat)
    return Point(float(longitude), float(latitude), srid=4326)


def district_containing(point: Point) -> District | None:
    return District.objects.filter(geometry__contains=point).first()


def village_containing(point: Point) -> Village | None:
    return Village.objects.filter(geometry__contains=point).first()


def districts_within_km(point: Point, km: float):
    """Districts whose centroid is within `km` of the point, nearest first.

    Uses a geodetic Distance annotation + filter, which is portable across
    SpatiaLite and PostGIS. On PostGIS this can also be expressed as a
    geography __dwithin for index acceleration.
    """
    return (District.objects.exclude(centroid__isnull=True)
            .annotate(distance=Distance("centroid", point))
            .filter(distance__lte=D(km=km))
            .order_by("distance"))


def nearest_districts(point: Point, limit: int = 5):
    return (District.objects.exclude(centroid__isnull=True)
            .annotate(distance=Distance("centroid", point))
            .order_by("distance")[:limit])
