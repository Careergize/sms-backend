from rest_framework import serializers

from .models import CatalogEntry


class CatalogEntrySerializer(serializers.ModelSerializer):
    skills = serializers.ListField(child=serializers.CharField(), required=False)
    body = serializers.ListField(child=serializers.CharField(), required=False)

    def validate_slug(self, value):
        if self.instance is not None and value != self.instance.slug:
            raise serializers.ValidationError("The catalogue slug cannot be changed.")
        return value

    class Meta:
        model = CatalogEntry
        fields = (
            "slug", "kind", "name", "label", "summary", "skills",
            "body", "fee", "hours",
        )


class CatalogEntryFilters(serializers.Serializer):
    kind = serializers.ChoiceField(choices=CatalogEntry.Kind.choices, required=False)
