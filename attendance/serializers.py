from django.utils import timezone
from rest_framework import serializers

from common.serializers import BranchFilterSerializer

from .models import Attendance

KINDS = ("students", "instructors")


class AttendanceQuery(BranchFilterSerializer):
    kind = serializers.ChoiceField(choices=KINDS, default="students")
    period = serializers.ChoiceField(choices=("day", "month"), default="day")
    date = serializers.DateField(default=timezone.localdate)


class AttendanceMark(serializers.Serializer):
    kind = serializers.ChoiceField(choices=KINDS)
    person = serializers.IntegerField(min_value=1, max_value=2**63 - 1)
    date = serializers.DateField()
    status = serializers.ChoiceField(choices=Attendance.Status.choices)

    def validate_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Attendance can only be marked for today or an earlier date.")
        return value
