from django.core.management.base import BaseCommand

from apps.analytics.matviews import refresh_all


class Command(BaseCommand):
    help = "Refresh materialized views (CONCURRENTLY on Postgres)."

    def handle(self, *args, **opts):
        result = refresh_all()
        self.stdout.write(self.style.SUCCESS(f"Refreshed: {result}"))
