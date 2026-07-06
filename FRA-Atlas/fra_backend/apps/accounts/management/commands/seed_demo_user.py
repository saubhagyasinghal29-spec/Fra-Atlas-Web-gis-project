"""Create a demo analyst account for the portal First Build (idempotent)."""
from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.common.enums import Designation


class Command(BaseCommand):
    help = "Create/refresh a demo analyst account (analyst / FraAtlas@2026)."

    def handle(self, *args, **opts):
        user, created = User.objects.get_or_create(
            username="analyst",
            defaults={"designation": Designation.STATE_COORDINATOR,
                      "is_staff": True, "email": "analyst@fra-atlas.gov.in"},
        )
        user.designation = Designation.STATE_COORDINATOR
        user.is_active = True
        user.set_password("FraAtlas@2026")
        user.save()
        msg = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{msg} demo user: analyst / FraAtlas@2026"))
