from decimal import Decimal

from rest_framework import serializers

from common.serializers import BranchFilterSerializer
from lessons.serializers import LessonSerializer

from .models import Student


class StudentSerializer(serializers.ModelSerializer):
    total_fee = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal(0), required=False, allow_null=True)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal(0), required=False, allow_null=True)

    class Meta:
        model = Student
        fields = (
            "id", "code", "name", "branch", "course", "status",
            "payment", "enrolled_on", "phone", "guardian_name", "guardian_phone",
            "instructor", "total_fee", "amount_paid",
        )

    def validate(self, attrs):
        fee = attrs.get("total_fee", getattr(self.instance, "total_fee", None))
        paid = attrs.get("amount_paid", getattr(self.instance, "amount_paid", None))
        if (fee is None) != (paid is None):
            raise serializers.ValidationError({"amount_paid": "Enter both the total fee and the amount paid, or leave both blank."})
        if fee is not None:
            if paid > fee:
                raise serializers.ValidationError({"amount_paid": "The amount paid cannot exceed the total fee."})
            attrs["payment"] = Student.Payment.PAID if paid == fee else Student.Payment.UNPAID
        return attrs


class StudentDetailSerializer(StudentSerializer):
    pending_amount = serializers.SerializerMethodField()
    instructor_name = serializers.CharField(source="instructor.name", read_only=True, default=None)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    branch_area = serializers.CharField(source="branch.area", read_only=True)
    lessons = serializers.SerializerMethodField()

    class Meta(StudentSerializer.Meta):
        fields = StudentSerializer.Meta.fields + ("pending_amount", "instructor_name", "branch_name", "branch_area", "lessons")

    def get_pending_amount(self, student):
        if student.total_fee is not None and student.amount_paid is not None:
            return str(student.total_fee - student.amount_paid)
        return None

    def get_lessons(self, student):
        lessons = student.lessons.select_related("instructor", "student", "vehicle_reservation__vehicle")
        return LessonSerializer(lessons, many=True).data


class StudentFilters(BranchFilterSerializer):
    payment = serializers.ChoiceField(choices=Student.Payment.choices, required=False)
    status = serializers.ChoiceField(choices=Student.Status.choices, required=False)
