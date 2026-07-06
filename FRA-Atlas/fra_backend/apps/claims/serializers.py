from rest_framework import serializers

from apps.claims.models import DSSRecommendation, FRAClaim


class DSSRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DSSRecommendation
        fields = ["id", "recommendation_type", "confidence_score", "supporting_factors"]


class FRAClaimSerializer(serializers.ModelSerializer):
    district_code = serializers.CharField(source="district.district_code", read_only=True)
    state = serializers.CharField(source="district.state", read_only=True)
    dss_recommendations = DSSRecommendationSerializer(many=True, read_only=True)

    class Meta:
        model = FRAClaim
        fields = [
            "id", "claim_identifier", "claim_type", "status",
            "tribal_community", "district", "district_code", "state", "village",
            "area_hectares", "claim_date", "forest_location_geojson",
            "status_history", "dss_recommendations_json", "dss_recommendations",
            "created_at", "updated_at",
        ]
        read_only_fields = ["claim_identifier", "status", "status_history", "created_at", "updated_at"]


class CreateClaimSerializer(serializers.Serializer):
    district = serializers.UUIDField()
    tribal_community = serializers.UUIDField()
    claim_type = serializers.CharField()
    area_hectares = serializers.DecimalField(max_digits=12, decimal_places=2)
    claim_date = serializers.DateField()
    village = serializers.UUIDField(required=False, allow_null=True)
    forest_location_geojson = serializers.JSONField(required=False, allow_null=True)
    reason = serializers.CharField(default="Initial creation")


class TransitionSerializer(serializers.Serializer):
    reason = serializers.CharField()
