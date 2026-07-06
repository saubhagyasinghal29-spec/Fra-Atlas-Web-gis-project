"""Data-subject rights endpoints (DPDP Act 2023)."""
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User
from apps.common.enums import Designation
from apps.privacy import services
from apps.privacy.models import DataSubjectRequest


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_data(request):
    """Right to access: export the caller's own personal data."""
    data = services.export_subject_data(request.user)
    DataSubjectRequest.objects.create(
        subject_user_id=request.user.id, request_type=DataSubjectRequest.Type.ACCESS,
        status=DataSubjectRequest.Status.COMPLETED, completed_at=timezone.now(),
    )
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def erase(request):
    """Right to erasure. A subject may request erasure of their own account; an
    admin (DISTRICT_ADMIN+/SUPERUSER) may process erasure for a named subject."""
    target_id = request.data.get("subject_user_id")
    if target_id and request.user.designation in (
            Designation.DISTRICT_ADMIN, Designation.STATE_COORDINATOR, Designation.SUPERUSER):
        subject = get_object_or_404(User, id=target_id)
    else:
        subject = request.user

    dsr = DataSubjectRequest.objects.create(
        subject_user_id=subject.id, request_type=DataSubjectRequest.Type.ERASURE,
        legal_basis_note="Claim records retained under statutory record-keeping; "
                         "account PII crypto-erased.",
    )
    result = services.erase_subject(subject, actor=request.user)
    dsr.status = DataSubjectRequest.Status.COMPLETED
    dsr.completed_at = timezone.now()
    dsr.result_json = {"pseudonym": result["pseudonym"]}
    dsr.save()
    return Response({"detail": "PII erased; claim records retained under legal basis.",
                     "request_id": str(dsr.id), "pseudonym": result["pseudonym"]})
