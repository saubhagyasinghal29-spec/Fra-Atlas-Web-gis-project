"""Document upload / download endpoints.

POST /api/v1/fra-claims/{claim_id}/documents/   multipart upload (validate, scan, OCR, store)
GET  /api/v1/fra-claims/{claim_id}/documents/   list
GET  /api/v1/documents/{attachment_id}/         download (signed URL / proxied bytes)
"""
import uuid

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.claims.models import FRAClaim
from apps.common.enums import Permission
from apps.documents import services
from apps.documents.models import (
    ALLOWED_CONTENT_TYPES,
    MAX_UPLOAD_BYTES,
    Attachment,
    ScanStatus,
)
from apps.documents.serializers import AttachmentSerializer
from apps.documents.sniff import sniff_content_type


def _claim_in_scope(user, claim):
    return user.in_scope(state=claim.state, district_code=claim.district_code)


class ClaimDocumentsView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, claim_id):
        claim = get_object_or_404(FRAClaim, id=claim_id)
        if not _claim_in_scope(request.user, claim):
            return Response({"detail": "Out of jurisdiction"}, status=403)
        qs = claim.attachments.all()
        return Response(AttachmentSerializer(qs, many=True).data)

    def post(self, request, claim_id):
        claim = get_object_or_404(FRAClaim, id=claim_id)
        if not request.user.has_fra_permission(Permission.EDIT_CLAIM):
            return Response({"detail": "EDIT_CLAIM permission required"}, status=403)
        if not _claim_in_scope(request.user, claim):
            return Response({"detail": "Out of jurisdiction"}, status=403)

        upload = request.FILES.get("file")
        if not upload:
            return Response({"detail": "No file provided"}, status=400)
        if upload.content_type not in ALLOWED_CONTENT_TYPES:
            return Response({"detail": f"Unsupported type {upload.content_type}. "
                             "Allowed: PDF, JPG, PNG."}, status=415)
        content = upload.read()
        sniffed = sniff_content_type(content)
        if sniffed not in ALLOWED_CONTENT_TYPES:
            return Response({"detail": "File content does not match an allowed type "
                             "(PDF, JPG, PNG). Detected: " + (sniffed or "unknown")},
                            status=415)
        if len(content) > MAX_UPLOAD_BYTES:
            return Response({"detail": "File exceeds 25MB limit"},
                            status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        scan_result = services.get_scanner().scan(content)
        if scan_result == ScanStatus.INFECTED:
            return Response({"detail": "File rejected: malware detected"}, status=422)

        sha = services.sha256_of(content)
        key = f"claims/{claim.id}/{uuid.uuid4()}_{upload.name}"
        services.get_storage().save(key, content)
        ocr_text = services.get_ocr().extract_text(content, upload.content_type)

        attachment = Attachment.objects.create(
            fra_claim=claim, filename=upload.name, content_type=upload.content_type,
            size_bytes=len(content), sha256=sha, storage_key=key,
            scan_status=scan_result, ocr_text=ocr_text,
            uploaded_by=request.user.id,
        )
        return Response(AttachmentSerializer(attachment).data,
                        status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_attachment(request, attachment_id):
    attachment = get_object_or_404(Attachment, id=attachment_id)
    claim = attachment.fra_claim
    if not _claim_in_scope(request.user, claim):
        return Response({"detail": "Out of jurisdiction"}, status=403)
    storage = services.get_storage()
    # In prod (S3) this returns a 302 to a signed URL; local backend streams bytes.
    content = storage.read(attachment.storage_key)
    resp = HttpResponse(content, content_type=attachment.content_type)
    resp["Content-Disposition"] = f'attachment; filename="{attachment.filename}"'
    return resp
