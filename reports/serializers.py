from rest_framework import serializers

from common.serializers import BranchFilterSerializer


class ReportFilters(BranchFilterSerializer):
    period = serializers.ChoiceField(choices=(1, 3, 6), default=6)
