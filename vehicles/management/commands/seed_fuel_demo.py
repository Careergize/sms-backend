from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from instructors.models import Instructor
from vehicles.models import FuelEntry, Vehicle
from vehicles.services import lock_vehicle

from .seed_vehicle_demo import DEMO_DAY, DEMO_VEHICLES


class Command(BaseCommand):
    help = "Add sample fuel fills to demo vehicles with empty fuel logs."

    @transaction.atomic
    def handle(self, *args, **options):
        final_day = min(DEMO_DAY, timezone.localdate())
        count = 0
        for branch_number in range(1, 6):
            branch = f"B{branch_number:02}"
            instructors = list(Instructor.objects.filter(branch_id=branch, code__startswith=f"INS-{branch}-")[:2])
            for index, (kind, name) in enumerate(DEMO_VEHICLES, start=1):
                vehicle = Vehicle.objects.filter(
                    registration=f"DEMO-{branch}-V{index}", branch_id=branch,
                    branch__is_active=True, name=name, kind=kind,
                ).first()
                if vehicle is None:
                    continue
                vehicle = lock_vehicle(vehicle.pk)
                if FuelEntry.objects.filter(vehicle=vehicle).exists():
                    continue

                fills = (
                    [(7, "4.5", 160, True), (4, "1.5", 90, False), (0, "2.8", 0, True)]
                    if kind == Vehicle.Kind.TWO_WHEELER else
                    [(7, "26.0", 420, True), (4, "8.5", 245, False), (0, "18.5", 0, True)]
                )
                if vehicle.odometer < fills[0][2]:
                    continue
                entries = [
                    FuelEntry(
                        vehicle=vehicle, branch_id=branch,
                        instructor=instructors[offset % len(instructors)] if instructors else None,
                        filled_on=final_day - timedelta(days=days), litres=Decimal(litres),
                        price_per_litre=Decimal("103.20") + Decimal("0.15") * (branch_number + offset),
                        odometer=vehicle.odometer - distance, full_tank=full,
                    )
                    for offset, (days, litres, distance, full) in enumerate(fills)
                ]
                FuelEntry.objects.bulk_create(entries)
                count += len(entries)
        self.stdout.write(self.style.SUCCESS(f"Added {count} demo fuel entries."))
