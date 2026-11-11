from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from common.serializers import BranchFilterSerializer

from .models import Lesson


class LessonSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name", read_only=True)
    instructor_name = serializers.CharField(source="instructor.name", read_only=True)
    branch = serializers.CharField(source="student.branch_id", read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    vehicle_registration = serializers.CharField(source="vehicle_reservation.vehicle.registration", read_only=True, default=None)

    def get_duration_minutes(self, lesson):
        return 60

    def validate_starts_at(self, value):
        if value.minute or value.second or value.microsecond:
            raise serializers.ValidationError("Lessons must start on the hour in Asia/Kolkata.")
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        Lesson.objects.filter(pk=instance.pk).update(starts_at=F("starts_at"))
        instance = Lesson.objects.get(pk=instance.pk)
        if any(getattr(instance, field) != validated_data[field] for field in (
            "student", "instructor", "starts_at",
        ) if field in validated_data) and hasattr(instance, "vehicle_reservation"):
            raise serializers.ValidationError("Remove the vehicle reservation before changing the lesson time, student, or instructor.")
        return super().update(instance, validated_data)

    class Meta:
        model = Lesson
        fields = (
            "id", "student", "student_name", "instructor", "instructor_name", "branch",
            "starts_at", "duration_minutes", "attendance", "vehicle_registration",
        )


class LessonFilters(BranchFilterSerializer):
    attendance = serializers.ChoiceField(choices=Lesson.Attendance.choices, required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        if "date_from" in attrs and "date_to" in attrs and attrs["date_from"] > attrs["date_to"]:
            raise serializers.ValidationError("date_to must be on or after date_from.")
        return attrs
