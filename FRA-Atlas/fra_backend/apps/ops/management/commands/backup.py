from django.core.management.base import BaseCommand

from apps.ops.backup import create_backup


class Command(BaseCommand):
    help = "Create a verified backup of system data."

    def handle(self, *args, **opts):
        snap = create_backup()
        status = self.style.SUCCESS if snap.verified else self.style.ERROR
        self.stdout.write(status(
            f"Backup {snap.id}: key={snap.storage_key} "
            f"rows={sum(snap.row_counts_json.values())} "
            f"hash={snap.content_hash[:12]} verified={snap.verified}"))
