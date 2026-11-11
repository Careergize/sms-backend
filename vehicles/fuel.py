from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response

from common.views import CollectionAPIView, DetailAPIView

from .models import FuelEntry
from .serializers import VehicleRecordFilter
from .services import lock_vehicle

CENT = Decimal("0.01")


def expense(entry):
    return (entry.litres * entry.price_per_litre).quantize(CENT, rounding=ROUND_HALF_UP)


def efficiencies(vehicle_ids):
    history = FuelEntry.objects.filter(vehicle_id__in=vehicle_ids).order_by("vehicle_id", "filled_on", "odometer", "pk")
    baseline = {}
    volume = defaultdict(Decimal)
    results = {}
    for entry in history:
        vehicle = entry.vehicle_id
        if vehicle in baseline:
            volume[vehicle] += entry.litres
        if entry.full_tank:
            if vehicle in baseline and entry.odometer > baseline[vehicle]:
                results[entry.pk] = str(
                    (Decimal(entry.odometer - baseline[vehicle]) / volume[vehicle]).quantize(CENT, rounding=ROUND_HALF_UP)
                )
            baseline[vehicle] = entry.odometer
            volume[vehicle] = Decimal(0)
    return results


class FuelFilter(VehicleRecordFilter):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        if "date_from" in attrs and "date_to" in attrs and attrs["date_from"] > attrs["date_to"]:
            raise serializers.ValidationError({"date_to": "End date must be on or after the start date."})
        return attrs


class FuelEntrySerializer(serializers.ModelSerializer):
    registration = serializers.CharField(source="vehicle.registration", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    instructor_name = serializers.CharField(source="instructor.name", read_only=True, default=None)
    litres = serializers.DecimalField(max_digits=8, decimal_places=3, min_value=Decimal("0.001"))
    price_per_litre = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=CENT)
    total_expense = serializers.SerializerMethodField()
    km_per_litre = serializers.SerializerMethodField()

    class Meta:
        model = FuelEntry
        fields = (
            "id", "vehicle", "registration", "branch", "branch_name", "instructor", "instructor_name",
            "filled_on", "litres", "price_per_litre", "odometer", "full_tank", "total_expense", "km_per_litre",
        )
        read_only_fields = ("branch",)

    def get_total_expense(self, entry):
        return str(expense(entry))

    def get_km_per_litre(self, entry):
        computed = self.context.get("efficiencies")
        if computed is None:
            computed = efficiencies([entry.vehicle_id])
        return computed.get(entry.pk)

    def validate_filled_on(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Enter today's date or an earlier filling date.")
        return value

    @transaction.atomic
    def save_entry(self, values, instance=None):
        vehicle = values.get("vehicle") or instance.vehicle
        vehicle_ids = {vehicle.pk}
        if instance is not None:
            vehicle_ids.add(instance.vehicle_id)
        locked = {pk: lock_vehicle(pk) for pk in sorted(vehicle_ids)}
        if instance is not None:
            current = FuelEntry.objects.select_for_update().get(pk=instance.pk)
            if current.vehicle_id != instance.vehicle_id:
                raise serializers.ValidationError("This fuel entry has moved to another vehicle. Reload and try again.")
            instance = current
        day = values.get("filled_on", getattr(instance, "filled_on", None))
        reading = values.get("odometer", getattr(instance, "odometer", None))
        conflicts = FuelEntry.objects.filter(vehicle=vehicle).filter(
            Q(filled_on__lt=day, odometer__gt=reading) | Q(filled_on__gt=day, odometer__lt=reading)
        )
        if instance is not None:
            conflicts = conflicts.exclude(pk=instance.pk)
        if conflicts.exists():
            raise serializers.ValidationError({"odometer": "The reading must follow the vehicle's fuel history in date order."})
        if instance is None or instance.vehicle_id != vehicle.pk:
            values["branch_id"] = locked[vehicle.pk].branch_id
        if instance is None:
            return super().create(values)
        return super().update(instance, values)

    def create(self, validated_data):
        return self.save_entry(validated_data)

    def update(self, instance, validated_data):
        return self.save_entry(validated_data, instance)


def summaries(entries):
    dimensions = {"branches": {}, "vehicles": {}, "instructors": {}}
    total = Decimal(0)
    litres = Decimal(0)
    for entry in entries:
        cost = expense(entry)
        total += cost
        litres += entry.litres
        groups = {
            "branches": (entry.branch_id, entry.branch.name),
            "vehicles": (entry.vehicle_id, entry.vehicle.registration),
            "instructors": (entry.instructor_id, entry.instructor.name if entry.instructor_id else "Unassigned"),
        }
        for dimension, (key, label) in groups.items():
            aggregate = dimensions[dimension].setdefault(key, {"name": label, "litres": Decimal(0), "total_expense": Decimal(0)})
            aggregate["litres"] += entry.litres
            aggregate["total_expense"] += cost

    def formatted(group):
        return {**group, "litres": str(group["litres"]), "total_expense": str(group["total_expense"])}

    return {
        "total_expense": str(total), "litres": str(litres), "count": len(entries),
        **{key: [formatted(row) for row in sorted(groups.values(), key=lambda row: (-row["total_expense"], row["name"]))]
           for key, groups in dimensions.items()},
    }


class FuelCollectionAPIView(CollectionAPIView):
    queryset = FuelEntry.objects.select_related("vehicle", "branch", "instructor")
    serializer_class = FuelEntrySerializer

    def get(self, request):
        filters = FuelFilter(data=request.query_params)
        filters.is_valid(raise_exception=True)
        mapping = {"branch_active": "branch__is_active", "date_from": "filled_on__gte", "date_to": "filled_on__lte"}
        entries = list(self.queryset.filter(**{
            mapping.get(key, key): value for key, value in filters.validated_data.items()
        }))
        rates = efficiencies({entry.vehicle_id for entry in entries})
        serializer = self.serializer_class(entries, many=True, context={"efficiencies": rates})
        return Response({"entries": serializer.data, "summary": summaries(entries)})


class FuelDetailAPIView(DetailAPIView):
    queryset = FuelCollectionAPIView.queryset
    serializer_class = FuelEntrySerializer
