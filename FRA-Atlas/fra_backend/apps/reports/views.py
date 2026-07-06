"""Report endpoints: async generate + status poll."""
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.enums import Permission
from apps.documents.services import get_storage
from apps.reports.models import ReportJob, ReportStatus
from apps.reports.tasks import generate_report


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate(request):
    if not request.user.has_fra_permission(Permission.VIEW_ANALYTICS):
        return Response({"detail": "VIEW_ANALYTICS permission required"}, status=403)
    job = ReportJob.objects.create(
        report_type=request.data.get("report_type", "district_claims"),
        export_format=request.data.get("export_format", "CSV").upper(),
        filters_json=request.data.get("filters", {}),
        requested_by=request.user.id,
        status=ReportStatus.QUEUED,
    )
    generate_report.delay(str(job.id))
    return Response({"job_id": str(job.id), "status": job.status},
                    status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def job_status(request, job_id):
    job = get_object_or_404(ReportJob, id=job_id)
    download_url = (f"/api/v1/reports/{job.id}/download/"
                    if job.status == ReportStatus.COMPLETE else None)
    return Response({
        "job_id": str(job.id), "status": job.status,
        "progress_percent": job.progress_percent,
        "download_url": download_url, "expires_at": job.expires_at,
        "error_message": job.error_message,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download(request, job_id):
    job = get_object_or_404(ReportJob, id=job_id)
    if job.status != ReportStatus.COMPLETE:
        return Response({"detail": "Report not ready"}, status=409)
    content = get_storage().read(job.storage_key)
    ctype = ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
             if job.export_format == "XLSX" else "text/csv")
    resp = HttpResponse(content, content_type=ctype)
    resp["Content-Disposition"] = f'attachment; filename="{job.report_type}.{job.export_format.lower()}"'
    return resp
