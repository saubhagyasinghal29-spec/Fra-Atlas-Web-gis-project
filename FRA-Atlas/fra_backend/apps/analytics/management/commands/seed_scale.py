"""Generate a large synthetic claim volume to validate performance at scale."""
import datetime
import random
import uuid

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.claims.models import FRAClaim
from apps.common.enums import ClaimStatus, ClaimType
from apps.geo.models import District, TribalCommunity


class Command(BaseCommand):
    help = "Bulk-create N synthetic FRA claims across all districts (perf testing)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=100000)
        parser.add_argument("--batch", type=int, default=5000)

    def handle(self, *args, **opts):
        n, batch = opts["count"], opts["batch"]
        districts = list(District.objects.all())
        # ensure each district has a community
        comms = {}
        for d in districts:
            c = d.communities.first() or TribalCommunity.objects.create(
                name_english=f"{d.name_english} Community", district=d)
            comms[d.id] = c
        statuses = [ClaimStatus.DRAFT, ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW,
                    ClaimStatus.APPROVED, ClaimStatus.REJECTED]
        created = 0
        timezone.now()
        while created < n:
            chunk = []
            for _ in range(min(batch, n - created)):
                d = random.choice(districts)
                idx = created + len(chunk)
                chunk.append(FRAClaim(
                    id=uuid.uuid4(),
                    claim_identifier=f"SCALE-{idx:08d}",
                    claim_type=random.choice(list(ClaimType.values)),
                    status=random.choice(statuses),
                    district=d, tribal_community=comms[d.id],
                    area_hectares=round(random.uniform(1, 200), 2),
                    claim_date=datetime.date(2024, 1, 1),
                    status_history=[],
                ))
            FRAClaim.objects.bulk_create(chunk, batch_size=batch)
            created += len(chunk)
            self.stdout.write(f"  {created}/{n}", ending="\r")
        self.stdout.write(self.style.SUCCESS(f"\nCreated {created} synthetic claims."))
