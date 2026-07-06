from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.auth import FRALoginView, LogoutView, MFASetupView, MFAVerifyView


def health(_request):
    """Liveness: process is up. Cheap, no dependencies."""
    return JsonResponse({"status": "ok"})


def ready(_request):
    """Readiness: can we serve traffic? Checks DB + cache."""
    from django.core.cache import cache
    from django.db import connections
    checks = {}
    ok = True
    try:
        connections["default"].cursor().execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as exc:  # noqa
        checks["database"] = f"error: {exc}"
        ok = False
    try:
        cache.set("_ready", "1", 5)
        checks["cache"] = "ok" if cache.get("_ready") == "1" else "error"
        ok = ok and checks["cache"] == "ok"
    except Exception as exc:  # noqa
        checks["cache"] = f"error: {exc}"
        ok = False
    return JsonResponse({"status": "ok" if ok else "degraded", "checks": checks},
                        status=200 if ok else 503)


urlpatterns = [
    path("health/", health),
    path("ready/", ready),
    path("", include("django_prometheus.urls")),  # /metrics
    path("admin/", admin.site.urls),
    path("api/v1/auth/login/", FRALoginView.as_view(), name="login"),
    path("api/v1/auth/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("api/v1/auth/mfa-setup/", MFASetupView.as_view(), name="mfa-setup"),
    path("api/v1/auth/mfa-verify/", MFAVerifyView.as_view(), name="mfa-verify"),
    path("api/v1/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/v1/", include("apps.claims.urls")),
    path("api/v1/", include("apps.analytics.urls")),
    path("api/v1/", include("apps.geo.urls")),
    path("api/v1/", include("apps.documents.urls")),
    path("api/v1/", include("apps.reports.urls")),
    path("api/v1/", include("apps.sync.urls")),
    path("api/v1/", include("apps.privacy.urls")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
