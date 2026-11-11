from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from common.serializers import BranchFilterSerializer
from students.models import Student

from .models import Assignment, Maintenance, Reservation, ServiceBill, Vehicle, VehicleMove
from .services import lock_vehicle, save_reservation

BILL_LIMIT = 5 * 1024 * 1024


class VehicleSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Vehicle
        fields = ("id", "registration", "name", "branch", "branch_name", "kind", "status", "odometer")

    def validate_registration(self, value):
        registration = value.upper()
        vehicles = Vehicle.objects.filter(registration=registration)
        if self.instance:
            vehicles = vehicles.exclude(pk=self.instance.pk)
        if vehicles.exists():
            raise serializers.ValidationError("This registration is already in the fleet.")
        return registration

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = lock_vehicle(instance.pk)
        branch = validated_data.get("branch", instance.branch)
        kind = validated_data.get("kind", instance.kind)
        if (branch.pk, kind) != (instance.branch_id, instance.kind) and instance.reservation_set.filter(
            ends_at__gt=timezone.now(),
        ).exists():
            raise serializers.ValidationError("Move future reservations before changing the vehicle branch or type.")
        return super().update(instance, validated_data)


class VehicleRecordFilter(BranchFilterSerializer):
    vehicle = serializers.IntegerField(required=False, min_value=1, max_value=2**63 - 1)
    instructor = serializers.IntegerField(required=False, min_value=1, max_value=2**63 - 1)


class ReservationFilter(VehicleRecordFilter):
    date = serializers.DateField(required=False)


class MaintenanceFilter(BranchFilterSerializer):
    vehicle = serializers.IntegerField(required=False, min_value=1, max_value=2**63 - 1)


class AssignmentSerializer(serializers.ModelSerializer):
    registration = serializers.CharField(source="vehicle.registration", read_only=True)
    instructor_name = serializers.CharField(source="instructor.name", read_only=True)

    class Meta:
        model = Assignment
        fields = (
            "id", "vehicle", "registration", "instructor", "instructor_name", "starts_on", "ends_on", "temporary",
            "handed_over_at", "handover_condition", "returned_at", "return_condition", "notes",
        )

    def validate(self, attrs):
        def get(key):
            return attrs.get(key, getattr(self.instance, key, None))

        start, end = get("starts_on"), get("ends_on")
        if start and end and start > end:
            raise serializers.ValidationError({"ends_on": "The assignment end date must be on or after its start date."})
        handed, returned = get("handed_over_at"), get("returned_at")
        if handed and not get("handover_condition"):
            raise serializers.ValidationError({"handover_condition": "Record the vehicle condition at handover."})
        if returned and (not handed or returned < handed or not get("return_condition")):
            raise serializers.ValidationError({"returned_at": "Record a handover first and enter the return condition and time."})
        if get("temporary") and not end:
            raise serializers.ValidationError({"ends_on": "Temporary assignments require an end date."})
        return attrs


class VehicleMoveSerializer(serializers.ModelSerializer):
    previous_vehicle = serializers.CharField(source="previous_vehicle.registration")
    next_vehicle = serializers.CharField(source="next_vehicle.registration")

    class Meta:
        model = VehicleMove
        fields = ("previous_vehicle", "next_vehicle", "changed_at", "reason")


class ReservationSerializer(serializers.ModelSerializer):
    starts_at = serializers.DateTimeField(required=False, allow_null=True)
    ends_at = serializers.DateTimeField(required=False, allow_null=True)
    registration = serializers.CharField(source="vehicle.registration", read_only=True)
    instructor_name = serializers.CharField(source="instructor.name", read_only=True, default=None)
    student_name = serializers.CharField(source="lesson.student.name", read_only=True, default=None)
    moves = VehicleMoveSerializer(many=True, read_only=True)
    reassignment_reason = serializers.CharField(required=False, allow_blank=True, max_length=300, write_only=True)
    new_student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), required=False, allow_null=True, write_only=True,
    )

    class Meta:
        model = Reservation
        fields = (
            "id", "vehicle", "registration", "lesson", "new_student", "student_name", "instructor", "instructor_name",
            "purpose", "starts_at", "ends_at", "used_at", "notes", "moves", "reassignment_reason",
        )

    def create(self, validated_data):
        return self.save_booking(validated_data)

    def update(self, instance, validated_data):
        return self.save_booking(validated_data, instance)

    def save_booking(self, data, instance=None):
        return save_reservation(
            data, instance, reason=data.pop("reassignment_reason", ""), new_student=data.pop("new_student", None),
        )


class MaintenanceSerializer(serializers.ModelSerializer):
    registration = serializers.CharField(source="vehicle.registration", read_only=True)
    cost = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal(0), required=False, allow_null=True)
    bill_name = serializers.SerializerMethodField()
    bill = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Maintenance
        fields = (
            "id", "vehicle", "registration", "kind", "scheduled_on", "completed_on", "service_provider",
            "provider_contact", "cost", "service_odometer", "next_due_on", "next_due_km", "notes", "bill", "bill_name",
        )

    def get_bill_name(self, record):
        if hasattr(record, "bill_name_cached"):
            return record.bill_name_cached
        return ServiceBill.objects.filter(maintenance=record).values_list("name", flat=True).first()

    def validate(self, attrs):
        completed = attrs.get("completed_on", getattr(self.instance, "completed_on", None))
        next_due = attrs.get("next_due_on", getattr(self.instance, "next_due_on", None))
        odometer = attrs.get("service_odometer", getattr(self.instance, "service_odometer", None))
        next_km = attrs.get("next_due_km", getattr(self.instance, "next_due_km", None))
        if completed and next_due and next_due < completed:
            raise serializers.ValidationError({"next_due_on": "The next service date cannot be before completion."})
        if odometer is not None and next_km is not None and next_km < odometer:
            raise serializers.ValidationError({"next_due_km": "The next service kilometre reading cannot be below the service reading."})
        return attrs

    def validate_bill(self, bill):
        if bill.size > BILL_LIMIT:
            raise serializers.ValidationError("Upload a bill no larger than 5 MB.")
        data = bill.read()
        signatures = {
            b"%PDF-": "application/pdf",
            b"\x89PNG\r\n\x1a\n": "image/png",
            b"\xff\xd8\xff": "image/jpeg",
        }
        for signature, content_type in signatures.items():
            if data.startswith(signature):
                return {"name": bill.name, "content_type": content_type, "data": data}
        raise serializers.ValidationError("Use a PDF, PNG, or JPEG bill.")

    @transaction.atomic
    def create(self, validated_data):
        bill = validated_data.pop("bill", None)
        record = super().create(validated_data)
        if bill:
            ServiceBill.objects.create(maintenance=record, **bill)
        return record

    @transaction.atomic
    def update(self, instance, validated_data):
        bill = validated_data.pop("bill", None)
        record = super().update(instance, validated_data)
        if bill:
            ServiceBill.objects.update_or_create(maintenance=record, defaults=bill)
            record.bill_name_cached = bill["name"]
        return record
