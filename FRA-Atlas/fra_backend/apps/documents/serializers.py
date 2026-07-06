from rest_framework import serializers

from apps.documents.models import Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["id", "filename", "content_type", "size_bytes", "sha256",
                  "scan_status", "ocr_text", "created_at"]
