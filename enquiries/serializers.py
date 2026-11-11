from rest_framework import serializers

from .models import Enquiry


class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = (
            "id", "name", "phone", "email", "programme", "message",
            "status", "created_at",
        )


class EnquiryFilters(serializers.Serializer):
    status = serializers.ChoiceField(choices=Enquiry.Status.choices, required=False)


class PublicEnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = ("name", "phone", "email", "programme", "message")
