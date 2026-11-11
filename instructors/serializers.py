from rest_framework import serializers

from common.serializers import BranchFilterSerializer

from .models import Instructor


class InstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instructor
        fields = (
            "id", "code", "name", "mobile", "email", "address",
            "branch", "experience_years", "licence_number", "licence_valid_until", "joined_on", "status",
        )


class InstructorFilters(BranchFilterSerializer):
    status = serializers.ChoiceField(choices=Instructor.Status.choices, required=False)
