from rest_framework.routers import DefaultRouter

from apps.claims.views import FRAClaimViewSet

router = DefaultRouter()
router.register("fra-claims", FRAClaimViewSet, basename="fra-claim")
urlpatterns = router.urls
