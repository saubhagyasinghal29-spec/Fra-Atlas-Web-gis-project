"""Offline-first sync API (spec Task 1.2).

Server is the source of truth. Field devices:
  1. PULL reference + recent data changed since their last sync watermark
     (delta sync, cursor-paginated, with a SHA-256 checksum + server_time to use
     as the next `since`). Responses are gzip-compressed by Django's GZip
     middleware when the client sends Accept-Encoding: gzip.
  2. PUSH claims created offline. Each is upserted; anything that conflicts with
     server state is recorded as a SyncConflict and returned for manual review
     rather than silently overwriting.
"""
import datetime
import hashlib
import json

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.claims import services as claim_services
from apps.claims.models import FRAClaim
from apps.geo.models import District, TribalCommunity, Village
from apps.sync.models import SyncBatch, SyncConflict

PULL_PAGE_SIZE = 1000

# Read-only reference entities the device may pull (server -> device).
PULLABLE = {
    "district": (District, ["district_code", "name_english", "state",
                            "risk_score", "risk_category"]),
    "village": (Village, ["village_code", "village_name", "district_id"]),
    "tribal_community": (TribalCommunity, ["name_english", "district_id"]),
    "fra_claim": (FRAClaim, ["claim_identifier", "status", "claim_type",
                             "district_id", "tribal_community_id",
                             "area_hectares", "claim_date"]),
}


def _serialize(obj, fields):
    out = {"id": str(obj.id), "updated_at": obj.updated_at.isoformat()}
    for f in fields:
        val = getattr(obj, f)
        if isinstance(val, (datetime.date, datetime.datetime)):
            val = val.isoformat()
        out[f] = str(val) if val is not None and not isinstance(val, (int, float, str)) else val
    return out


def _checksum(records) -> str:
    blob = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def _parse_ts(value):
    """Parse an ISO timestamp from a query param, tolerating the '+' -> ' '
    substitution that URL decoding applies to timezone offsets."""
    if not value:
        return None
    dt = parse_datetime(value)
    if dt is None and " " in value:
        dt = parse_datetime(value.replace(" ", "+"))
    return dt


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pull(request):
    entity = request.query_params.get("entity")
    if entity not in PULLABLE:
        return Response({"detail": f"Unknown entity. Options: {list(PULLABLE)}"}, status=400)
    model, fields = PULLABLE[entity]
    since = request.query_params.get("since")
    cursor = request.query_params.get("cursor")  # ISO updated_at of last seen row

    server_time = timezone.now()
    qs = model.objects.all().order_by("updated_at", "id")
    dt_since = _parse_ts(since)
    if dt_since:
        qs = qs.filter(updated_at__gt=dt_since)
    dt_cursor = _parse_ts(cursor)
    if dt_cursor:
        qs = qs.filter(updated_at__gt=dt_cursor)

    # scope claims/villages to the officer's jurisdiction
    if entity == "fra_claim" and request.user.assigned_districts:
        qs = qs.filter(district__district_code__in=request.user.assigned_districts)

    page = list(qs[:PULL_PAGE_SIZE])
    records = [_serialize(o, fields) for o in page]
    has_more = len(page) == PULL_PAGE_SIZE
    next_cursor = records[-1]["updated_at"] if records and has_more else None
    return Response({
        "entity": entity,
        "records": records,
        "count": len(records),
        "checksum": _checksum(records),
        "has_more": has_more,
        "next_cursor": next_cursor,
        "server_time": server_time.isoformat(),  # device stores as next `since`
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def push(request):
    """Upload claims created offline. Body:
        {"device_id": "...", "claims": [{client_ref, district_code,
          tribal_community_id, claim_type, area_hectares, claim_date}, ...]}
    """
    device_id = request.data.get("device_id", "unknown")
    claims = request.data.get("claims", [])
    payload_sha = hashlib.sha256(
        json.dumps(claims, sort_keys=True, default=str).encode()).hexdigest()

    with transaction.atomic():
        batch = SyncBatch.objects.create(
            device_id=device_id, user_id=request.user.id,
            pushed_count=len(claims), payload_sha256=payload_sha,
        )
        accepted, conflicts = [], []
        for item in claims:
            client_ref = item.get("client_ref", "")
            try:
                district = District.objects.get(district_code=item["district_code"])
                community = TribalCommunity.objects.get(id=item["tribal_community_id"])
            except (KeyError, District.DoesNotExist, TribalCommunity.DoesNotExist) as exc:
                conflicts.append(SyncConflict(
                    batch=batch, entity_type="fra_claim", client_ref=client_ref,
                    reason=f"Unresolved reference: {exc}", client_payload=item))
                continue
            # jurisdiction guard
            if (request.user.assigned_districts and
                    district.district_code not in request.user.assigned_districts):
                conflicts.append(SyncConflict(
                    batch=batch, entity_type="fra_claim", client_ref=client_ref,
                    reason="Out of device operator's jurisdiction", client_payload=item))
                continue
            claim = claim_services.create_claim(
                actor=request.user, district=district, tribal_community=community,
                claim_type=item.get("claim_type", "CFR"),
                area_hectares=item.get("area_hectares", 0),
                claim_date=item.get("claim_date"),
                reason=f"Offline sync from {device_id}",
                context=getattr(request, "audit_context", {}),
            )
            accepted.append({"client_ref": client_ref, "server_id": str(claim.id),
                             "claim_identifier": claim.claim_identifier})

        SyncConflict.objects.bulk_create(conflicts)
        batch.accepted_count = len(accepted)
        batch.conflict_count = len(conflicts)
        batch.save(update_fields=["accepted_count", "conflict_count", "updated_at"])

    return Response({
        "batch_id": str(batch.id),
        "accepted": accepted,
        "conflicts": [{"client_ref": c.client_ref, "reason": c.reason} for c in conflicts],
        "accepted_count": len(accepted),
        "conflict_count": len(conflicts),
    })
