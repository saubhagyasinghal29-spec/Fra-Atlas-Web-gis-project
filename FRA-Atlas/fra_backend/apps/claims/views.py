"""FRA claim API. Querysets are auto-scoped to the requesting user's
jurisdiction; transitions enforce the required permission + state machine and
write audit entries via the service layer.
"""
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import HasFRAPermission
from apps.claims import services
from apps.claims.models import FRAClaim
from apps.claims.serializers import (
    CreateClaimSerializer,
    FRAClaimSerializer,
    TransitionSerializer,
)
from apps.common.api_hardening import ETagMixin, IdempotencyMixin
from apps.common.enums import ClaimStatus, Designation, Permission
from apps.geo.models import District, TribalCommunity, Village


class FRAClaimViewSet(IdempotencyMixin, ETagMixin, viewsets.ModelViewSet):
    serializer_class = FRAClaimSerializer
    permission_classes = [IsAuthenticated, HasFRAPermission]
    required_permission = Permission.VIEW_CLAIM

    def get_queryset(self):
        qs = FRAClaim.objects.select_related("district", "tribal_community").all()
        user = self.request.user
        if user.designation == Designation.SUPERUSER:
            return qs
        districts = user.assigned_districts or []
        states = user.assigned_states or []
        if districts:
            qs = qs.filter(district__district_code__in=districts)
        elif states:
            qs = qs.filter(district__state__in=states)
        else:
            qs = qs.none()
        # optional filters
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def create(self, request, *args, **kwargs):
        return self.idempotent(request, self._create)

    def _create(self, request, *args, **kwargs):
        if not request.user.has_fra_permission(Permission.CREATE_CLAIM):
            return Response({"detail": "CREATE_CLAIM permission required"}, status=403)
        serializer = CreateClaimSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        district = get_object_or_404(District, id=data["district"])
        community = get_object_or_404(TribalCommunity, id=data["tribal_community"])
        village = (get_object_or_404(Village, id=data["village"])
                   if data.get("village") else None)
        claim = services.create_claim(
            actor=request.user, district=district, tribal_community=community,
            claim_type=data["claim_type"], area_hectares=data["area_hectares"],
            claim_date=data["claim_date"], village=village,
            forest_location_geojson=data.get("forest_location_geojson"),
            reason=data["reason"], context=getattr(request, "audit_context", {}),
        )
        return Response(FRAClaimSerializer(claim).data, status=status.HTTP_201_CREATED)

    def _transition(self, request, pk, to_status, permission_code):
        claim = self.get_object()
        if not request.user.has_fra_permission(permission_code):
            return Response({"detail": f"{permission_code} permission required"}, status=403)
        serializer = TransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            claim = services.transition_claim(
                claim=claim, to_status=to_status, actor=request.user,
                reason=serializer.validated_data["reason"],
                context=getattr(request, "audit_context", {}),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(FRAClaimSerializer(claim).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        return self._transition(request, pk, ClaimStatus.SUBMITTED, Permission.SUBMIT_CLAIM)

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        return self._transition(request, pk, ClaimStatus.UNDER_REVIEW, Permission.REVIEW_CLAIM)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._transition(request, pk, ClaimStatus.APPROVED, Permission.APPROVE_CLAIM)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._transition(request, pk, ClaimStatus.REJECTED, Permission.REJECT_CLAIM)

    @action(detail=True, methods=["get", "post"], url_path="dss-recommendations")
    def dss_recommendations(self, request, pk=None):
        """GET lists stored recommendations; POST (re)generates them via the DSS engine."""
        from apps.analytics.dss import generate_and_store
        from apps.claims.serializers import DSSRecommendationSerializer

        claim = self.get_object()
        if request.method == "POST":
            if not request.user.has_fra_permission(Permission.VIEW_ANALYTICS):
                return Response({"detail": "VIEW_ANALYTICS permission required"}, status=403)
            generate_and_store(claim)
        recs = claim.dss_recommendations.all()
        return Response({
            "claim_identifier": claim.claim_identifier,
            "count": recs.count(),
            "recommendations": DSSRecommendationSerializer(recs, many=True).data,
        })
