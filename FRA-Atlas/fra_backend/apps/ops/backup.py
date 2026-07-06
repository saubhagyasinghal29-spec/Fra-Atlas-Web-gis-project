"""Real, verifiable backup & restore.

Fixes the audit-Critical finding that the old snapshot task wrote no data and
self-asserted verification. Two backends:

* ``logical`` (default): Django serialization of all app data to JSON, stored via
  the configured storage backend, hashed, then **re-read from storage and
  hash-verified** before the snapshot is marked verified. Restorable via loaddata.
  Portable across SQLite/SpatiaLite/PostGIS and fully testable in-process.
* ``pg_dump`` (BACKUP_BACKEND=pg_dump): physical ``pg_dump -Fc`` for production
  Postgres, restored with ``pg_restore``. Used at real scale.

Either way a DataSnapshot row records the real storage key, row counts, content
hash, and a verified flag set only after a successful read-back.
"""
import gzip
import hashlib
import subprocess

from django.apps import apps as django_apps
from django.conf import settings
from django.core import serializers
from django.utils import timezone

from apps.documents.services import get_storage
from apps.ops.models import DataSnapshot

# App models included in a logical backup (data of record; excludes audit log,
# which is exported separately and never overwritten on restore).
BACKUP_APPS = ["geo", "claims", "accounts", "analytics", "documents",
               "reports", "ops", "sync"]


def _iter_models():
    for app_label in BACKUP_APPS:
        yield from django_apps.get_app_config(app_label).get_models()


def _row_counts():
    counts = {}
    for model in _iter_models():
        mgr = getattr(model, "all_objects", model.objects)
        counts[model._meta.label] = mgr.count()
    return counts


def _logical_dump() -> bytes:
    objects = []
    for model in _iter_models():
        mgr = getattr(model, "all_objects", model.objects)
        objects.extend(mgr.all())
    data = serializers.serialize("json", objects)
    return gzip.compress(data.encode())


def create_backup() -> DataSnapshot:
    """Produce a backup, store it, read it back, verify its hash, record it."""
    backend = getattr(settings, "BACKUP_BACKEND", "logical")
    now = timezone.now()
    counts = _row_counts()

    if backend == "pg_dump":
        payload, ext = _pg_dump(), "dump"
    else:
        payload, ext = _logical_dump(), "json.gz"

    content_hash = hashlib.sha256(payload).hexdigest()
    key = f"backups/{now:%Y%m%dT%H%M%S}.{ext}"
    storage = get_storage()
    storage.save(key, payload)

    # Verify: read back from storage and re-hash. Only then mark verified.
    readback = storage.read(key)
    verified = hashlib.sha256(readback).hexdigest() == content_hash and len(readback) == len(payload)

    return DataSnapshot.objects.create(
        content_hash=content_hash, row_counts_json=counts,
        storage_key=key, verified=verified,
    )


def _pg_dump() -> bytes:  # pragma: no cover - requires live pg + creds
    db = settings.DATABASES["default"]
    cmd = ["pg_dump", "-Fc", "-h", db.get("HOST", "localhost"),
           "-p", str(db.get("PORT", 5432)), "-U", db["USER"], db["NAME"]]
    env = {"PGPASSWORD": db.get("PASSWORD", "")}
    import os
    proc = subprocess.run(cmd, capture_output=True, env={**os.environ, **env}, check=True)
    return proc.stdout


def restore_logical(snapshot: DataSnapshot) -> dict:
    """Restore a logical backup with loaddata semantics (idempotent upsert by pk).
    Returns the row counts after restore. Never touches the audit log."""
    payload = get_storage().read(snapshot.storage_key)
    data = gzip.decompress(payload).decode()
    restored = 0
    for obj in serializers.deserialize("json", data, ignorenonexistent=True):
        obj.save()
        restored += 1
    return {"restored_objects": restored, "row_counts": _row_counts()}
