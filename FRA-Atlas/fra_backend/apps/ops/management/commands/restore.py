from django.core.management.base import BaseCommand, CommandError

from apps.ops.backup import restore_logical
from apps.ops.models import DataSnapshot


class Command(BaseCommand):
    help = "Restore data from a logical backup snapshot."

    def add_arguments(self, parser):
        parser.add_argument("snapshot_id")

    def handle(self, *args, **opts):
        snap = DataSnapshot.objects.filter(id=opts["snapshot_id"]).first()
        if not snap:
            raise CommandError("Snapshot not found")
        result = restore_logical(snap)
        self.stdout.write(self.style.SUCCESS(
            f"Restored {result['restored_objects']} objects from {snap.storage_key}"))
