from datetime import timedelta

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from lessons.models import Lesson

from .models import Reservation, Vehicle, VehicleMove


def lock_vehicle(pk):
    # A write locks the row on PostgreSQL and acquires SQLite's writer lock before checking availability.
    if not Vehicle.objects.filter(pk=pk).update(odometer=F("odometer")):
        raise ValidationError({"vehicle": "This vehicle no longer exists."})
    return Vehicle.objects.get(pk=pk)


@transaction.atomic
def save_reservation(values, instance=None, reason="", new_student=None):
    requested_vehicle = values.get("vehicle") or instance.vehicle
    vehicle = lock_vehicle(requested_vehicle.pk)
    if instance:
        current = Reservation.objects.select_for_update().get(pk=instance.pk)
        if current.vehicle_id != instance.vehicle_id:
            raise ValidationError("This reservation has already been reassigned. Reload and try again.")
        instance = current

    def get(field, default=None):
        return values.get(field, getattr(instance, field, default))

    purpose = get("purpose")
    lesson = get("lesson")
    if new_student is not None:
        if instance or lesson is not None or purpose != Reservation.Purpose.LESSON:
            raise ValidationError({"new_student": "Select either an existing lesson or a student for a new lesson."})
        instructor = get("instructor")
        start = get("starts_at")
        if instructor is None or start is None or start.minute or start.second or start.microsecond:
            raise ValidationError({"starts_at": "A new lesson requires an instructor and an hourly start time."})
        if Lesson.objects.filter(starts_at=start).filter(
            Q(student=new_student) | Q(instructor=instructor)
        ).exists():
            raise ValidationError({"starts_at": "The student or instructor already has a lesson at this time."})
        lesson = Lesson.objects.create(student=new_student, instructor=instructor, starts_at=start)
    if (purpose == Reservation.Purpose.LESSON) != (lesson is not None):
        raise ValidationError({"lesson": "Select a lesson only when the purpose is Driving lesson."})
    if lesson is not None:
        if not Lesson.objects.filter(pk=lesson.pk).update(starts_at=F("starts_at")):
            raise ValidationError({"lesson": "This lesson no longer exists."})
        lesson = Lesson.objects.select_related("student").get(pk=lesson.pk)
        if lesson.student.branch_id != vehicle.branch_id:
            raise ValidationError({"vehicle": "Select a vehicle from the student's branch."})
        course = lesson.student.course
        if (course in Vehicle.Kind.values and vehicle.kind != course) or (course == "refresher" and vehicle.kind == Vehicle.Kind.TWO_WHEELER):
            raise ValidationError({"vehicle": "Select a vehicle that matches the student's course."})
        values.update(
            lesson=lesson, starts_at=lesson.starts_at,
            ends_at=lesson.starts_at + timedelta(hours=1), instructor=lesson.instructor,
        )
    start, end = get("starts_at"), get("ends_at")
    if start is None or end is None or start >= end:
        raise ValidationError({"ends_at": "Enter a start and a later end time."})
    if purpose != Reservation.Purpose.BLOCK and vehicle.status != Vehicle.Status.ACTIVE:
        unchanged_slot = instance and (
            vehicle.pk, start, end, purpose
        ) == (instance.vehicle_id, instance.starts_at, instance.ends_at, instance.purpose)
        if not unchanged_slot:
            raise ValidationError({"vehicle": "This vehicle is not active."})

    used = get("used_at")
    if used is not None and (
        purpose == Reservation.Purpose.BLOCK or get("instructor") is None
        or not start <= used < end or used > timezone.now()
    ):
        raise ValidationError({"used_at": "Record an instructor and a usage time within the reservation that has already occurred."})
    if instance and instance.used_at and (
        vehicle.pk, start, end, purpose, getattr(get("instructor"), "pk", None), getattr(lesson, "pk", None)
    ) != (instance.vehicle_id, instance.starts_at, instance.ends_at, instance.purpose, instance.instructor_id, instance.lesson_id):
        raise ValidationError("A reservation with recorded usage cannot change its vehicle, time, purpose, lesson, or instructor.")

    conflicts = Reservation.objects.filter(vehicle=vehicle, starts_at__lt=end, ends_at__gt=start)
    if instance:
        conflicts = conflicts.exclude(pk=instance.pk)
    if conflicts.exists():
        raise ValidationError({"vehicle": "The vehicle is already booked or blocked during this time."})

    if not instance:
        return Reservation.objects.create(**values)
    previous = instance.vehicle
    if previous.pk != vehicle.pk and not reason:
        raise ValidationError({"reassignment_reason": "Enter a reason for moving this reservation to another vehicle."})
    for field, value in values.items():
        setattr(instance, field, value)
    instance.save()
    if previous.pk != vehicle.pk:
        VehicleMove.objects.create(reservation=instance, previous_vehicle=previous, next_vehicle=vehicle, reason=reason)
    return instance
