from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from branches.models import Branch
from instructors.models import Instructor
from lessons.models import Lesson
from vehicles.models import Assignment, Maintenance, Reservation, Vehicle
from vehicles.services import save_reservation

DEMO_DAY = date(2026, 11, 9)
DEMO_VEHICLES = (
    (Vehicle.Kind.MANUAL, "Demo manual training car"),
    (Vehicle.Kind.AUTOMATIC, "Demo automatic training car"),
    (Vehicle.Kind.TWO_WHEELER, "Demo training scooter"),
)


def reserve_example(vehicle, **values):
    if Reservation.objects.filter(vehicle=vehicle, purpose=values["purpose"], starts_at=values["starts_at"]).exists():
        return
    try:
        save_reservation({"vehicle": vehicle, **values})
    except ValidationError:
        # Preserve any real reservation already occupying the demo time.
        return


class Command(BaseCommand):
    help = "Add illustrative vehicles, assignments, reservations, and maintenance without overwriting records."

    @transaction.atomic
    def handle(self, *args, **options):
        for branch in Branch.objects.filter(is_active=True, code__in=["B01", "B02", "B03", "B04", "B05"]):
            instructors = list(Instructor.objects.filter(branch=branch, status=Instructor.Status.ACTIVE)[:2])
            for index, (kind, name) in enumerate(DEMO_VEHICLES, start=1):
                vehicle, _ = Vehicle.objects.get_or_create(
                    registration=f"DEMO-{branch.pk}-V{index}", defaults={
                        "name": name, "branch": branch, "kind": kind, "odometer": 7400 + index * 950,
                    },
                )
                if vehicle.branch_id != branch.pk or vehicle.name != name:
                    continue
                for instructor in instructors[:2 if index == 1 else 1]:
                    Assignment.objects.get_or_create(
                        vehicle=vehicle, instructor=instructor, starts_on=DEMO_DAY - timedelta(days=7),
                        defaults={"handover_condition": "Demo handover. Clean vehicle, no visible damage.",
                                  "handed_over_at": timezone.make_aware(datetime.combine(DEMO_DAY - timedelta(days=7), time(8)))},
                    )
                for offset, work in enumerate(Maintenance.Kind.values[index - 1::len(DEMO_VEHICLES)]):
                    scheduled = DEMO_DAY - timedelta(days=10 + offset * 5)
                    Maintenance.objects.get_or_create(
                        vehicle=vehicle, kind=work, scheduled_on=scheduled,
                        defaults={"completed_on": scheduled, "service_provider": "Demo Workshop",
                                  "provider_contact": "service@example.com", "cost": 850 + offset * 550,
                                  "service_odometer": vehicle.odometer, "next_due_on": DEMO_DAY + timedelta(days=90),
                                  "next_due_km": vehicle.odometer + 5000, "notes": "Illustrative maintenance entry."},
                    )
                lesson = Lesson.objects.filter(
                    student__branch=branch, student__course=kind, starts_at__date=DEMO_DAY,
                    vehicle_reservation__isnull=True,
                ).first()
                if lesson:
                    reserve_example(vehicle, purpose=Reservation.Purpose.LESSON, lesson=lesson, starts_at=lesson.starts_at)
                start = timezone.make_aware(datetime.combine(DEMO_DAY, time(17 + index)))
                purpose = (Reservation.Purpose.BLOCK, Reservation.Purpose.TEST, Reservation.Purpose.BOOKING)[index - 1]
                reserve_example(vehicle, purpose=purpose, starts_at=start, ends_at=start + timedelta(hours=1),
                                instructor=instructors[0] if instructors and purpose != Reservation.Purpose.BLOCK else None,
                                notes="Illustrative reservation.")
        self.stdout.write(self.style.SUCCESS("Demo fleet is ready."))
