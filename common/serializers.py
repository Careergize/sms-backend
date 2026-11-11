from rest_framework import serializers


class QueryBooleanField(serializers.BooleanField):
    default_empty_html = serializers.empty


class BranchFilterSerializer(serializers.Serializer):
    branch = serializers.SlugField(required=False, max_length=16)
    branch_active = QueryBooleanField(required=False)
