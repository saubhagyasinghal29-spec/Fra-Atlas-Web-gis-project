from django.urls import path

from apps.reports import views

urlpatterns = [
    path("reports/generate/", views.generate),
    path("reports/<uuid:job_id>/status/", views.job_status),
    path("reports/<uuid:job_id>/download/", views.download),
]
