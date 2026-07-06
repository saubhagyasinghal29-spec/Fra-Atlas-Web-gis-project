from django.urls import path

from apps.geo import views

urlpatterns = [
    path("geospatial/districts/", views.districts_geojson),
    path("geospatial/point-in-polygon/", views.point_in_polygon),
    path("geospatial/nearby/", views.nearby_districts),
]
