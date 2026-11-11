from django.db import models
from django.db.models import F, Q


class Vehicle(models.Model):
    class Kind(models.TextChoices):
        MANUAL = "manual", "Manual car"
        AUTOMATIC = "automatic", "Automatic car"
        TWO_WHEELER = "two-wheeler", "Two-wheeler"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        MAINTENANCE = "maintenance", "In maintenance"
        INACTIVE = "inactive", "Inactive"

    registration = models.CharField(max_length=24, unique=True)
    name = models.CharField(max_length=100)
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT)
    kind = models.CharField(max_length=12, choices=Kind)
    status = models.CharField(max_length=12, choices=Status, default=Status.ACTIVE)
    odometer = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("registration",)


class Assignment(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    instructor = models.ForeignKey("instructors.Instructor", on_delete=models.PROTECT)
    starts_on = models.DateField()
    ends_on = models.DateField(null=True, blank=True)
    temporary = models.BooleanField(default=False)
    handed_over_at = models.DateTimeField(null=True, blank=True)
    handover_condition = models.TextField(blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    return_condition = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-starts_on", "-pk")
        constraints = [
            models.CheckConstraint(condition=Q(ends_on__isnull=True) | Q(ends_on__gte=F("starts_on")), name="vehicle_assignment_dates"),
        ]


class Reservation(models.Model):
    class Purpose(models.TextChoices):
        LESSON = "lesson", "Driving lesson"
        BOOKING = "booking", "Vehicle booking"
        TEST = "test", "Driving test"
        BLOCK = "block", "Unavailable / blocked"

    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    lesson = models.OneToOneField("lessons.Lesson", on_delete=models.CASCADE, related_name="vehicle_reservation", null=True, blank=True)
    instructor = models.ForeignKey("instructors.Instructor", on_delete=models.PROTECT, null=True, blank=True)
    purpose = models.CharField(max_length=8, choices=Purpose)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("starts_at", "pk")
        indexes = [models.Index(fields=("vehicle", "starts_at", "ends_at"))]
        constraints = [
            models.CheckConstraint(condition=Q(ends_at__gt=F("starts_at")), name="vehicle_reservation_times"),
            models.CheckConstraint(
                condition=Q(purpose="lesson", lesson__isnull=False) | (~Q(purpose="lesson") & Q(lesson__isnull=True)),
                name="vehicle_reservation_lesson_link",
            ),
        ]


class VehicleMove(models.Model):
    reservation = models.ForeignKey(Reservation, related_name="moves", on_delete=models.CASCADE)
    previous_vehicle = models.ForeignKey(Vehicle, related_name="+", on_delete=models.PROTECT)
    next_vehicle = models.ForeignKey(Vehicle, related_name="+", on_delete=models.PROTECT)
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=300)


class Maintenance(models.Model):
    class Kind(models.TextChoices):
        SERVICE = "service", "Regular service"
        OIL = "oil", "Oil change"
        TYRE = "tyre", "Tyre replacement"
        BATTERY = "battery", "Battery replacement"
        BRAKES = "brakes", "Brake inspection"
        ENGINE = "engine", "Engine maintenance"
        REPAIR = "repair", "General repair"
        ACCIDENT = "accident", "Accident repair"

    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    kind = models.CharField(max_length=10, choices=Kind)
    scheduled_on = models.DateField()
    completed_on = models.DateField(null=True, blank=True)
    service_provider = models.CharField(max_length=160, blank=True)
    provider_contact = models.CharField(max_length=120, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    service_odometer = models.PositiveIntegerField(null=True, blank=True)
    next_due_on = models.DateField(null=True, blank=True)
    next_due_km = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-scheduled_on", "-pk")


class ServiceBill(models.Model):
    maintenance = models.OneToOneField(Maintenance, on_delete=models.CASCADE, related_name="bill")
    name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=32)
    data = models.BinaryField()


class FuelEntry(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT)
    instructor = models.ForeignKey("instructors.Instructor", on_delete=models.PROTECT, null=True, blank=True)
    filled_on = models.DateField()
    litres = models.DecimalField(max_digits=8, decimal_places=3)
    price_per_litre = models.DecimalField(max_digits=8, decimal_places=2)
    odometer = models.PositiveIntegerField()
    full_tank = models.BooleanField(default=True)

    class Meta:
        ordering = ("-filled_on", "-odometer", "-pk")
        indexes = [models.Index(fields=("vehicle", "filled_on", "odometer"))]
        constraints = [
            models.CheckConstraint(condition=Q(litres__gt=0), name="fuel_positive_litres"),
            models.CheckConstraint(condition=Q(price_per_litre__gt=0), name="fuel_positive_price"),
        ]
