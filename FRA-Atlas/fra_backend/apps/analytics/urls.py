from django.urls import path

from apps.analytics import views

urlpatterns = [
    path("analytics/districts/", views.districts_atlas),
    path("analytics/risk-model/status/", views.risk_model_status),
    path("analytics/factor-correlation/", views.factor_correlation),
    path("analytics/predict-district-risk/", views.predict_district_risk),
    path("analytics/pca-clustering/", views.pca_clustering),
    path("districts/<str:district_code>/risk/", views.district_risk),
    path("districts/<str:district_code>/claims/summary/", views.district_claims_summary),
]
