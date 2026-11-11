from rest_framework import serializers

from common.serializers import QueryBooleanField

from .models import Branch


class BranchSerializer(serializers.ModelSerializer):
    def validate_code(self, value):
        if self.instance is not None and value != self.instance.code:
            raise serializers.ValidationError("The branch code cannot be changed.")
        return value

    class Meta:
        model = Branch
        fields = (
            "code", "name", "area", "is_active",
        )


class BranchFilters(serializers.Serializer):
    is_active = QueryBooleanField(required=False)
