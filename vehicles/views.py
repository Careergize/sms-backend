from datetime import datetime, time, timedelta
from io import BytesIO

from django.db.models import OuterRef, Prefetch, Subquery
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from common.serializers import BranchFilterSerializer
from common.views import CollectionAPIView, DetailAPIView

from .models import Assignment, Maintenance, Reservation, ServiceBill, Vehicle, VehicleMove
from .serializers import (
    AssignmentSerializer, MaintenanceFilter, MaintenanceSerializer, ReservationFilter,
    ReservationSerializer, VehicleRecordFilter, VehicleSerializer,
)


class VehicleCollectionAPIView(CollectionAPIView):
    queryset = Vehicle.objects.select_related("branch")
    serializer_class = VehicleSerializer
    filter_serializer_class = BranchFilterSerializer
    filters = {"branch_active": "branch__is_active"}


class VehicleDetailAPIView(DetailAPIView):
    queryset = Vehicle.objects.select_related("branch")
    serializer_class = VehicleSerializer


class AssignmentCollectionAPIView(CollectionAPIView):
    queryset = Assignment.objects.select_related("vehicle", "instructor")
    serializer_class = AssignmentSerializer
    filter_serializer_class = VehicleRecordFilter
    filters = {"branch": "vehicle__branch_id", "branch_active": "vehicle__branch__is_active"}


class AssignmentDetailAPIView(DetailAPIView):
    queryset = AssignmentCollectionAPIView.queryset
    serializer_class = AssignmentSerializer


class ReservationCollectionAPIView(CollectionAPIView):
    queryset = Reservation.objects.select_related("vehicle", "instructor", "lesson__student").prefetch_related(
        Prefetch("moves", queryset=VehicleMove.objects.select_related("previous_vehicle", "next_vehicle").order_by("changed_at")),
    )
    serializer_class = ReservationSerializer
    filter_serializer_class = ReservationFilter
    filters = {"branch": "vehicle__branch_id", "branch_active": "vehicle__branch__is_active"}

    def get(self, request):
        params = ReservationFilter(data=request.query_params)
        params.is_valid(raise_exception=True)
        filters = dict(params.validated_data)
        day = filters.pop("date", None)
        records = self.queryset.filter(**{self.filters.get(key, key): value for key, value in filters.items()})
        if day:
            start = timezone.make_aware(datetime.combine(day, time.min))
            end = start + timedelta(days=1)
            records = records.filter(starts_at__lt=end, ends_at__gt=start)
        return Response(self.serializer_class(records, many=True).data)


class ReservationDetailAPIView(DetailAPIView):
    queryset = ReservationCollectionAPIView.queryset
    serializer_class = ReservationSerializer


class MaintenanceCollectionAPIView(CollectionAPIView):
    queryset = Maintenance.objects.select_related("vehicle").annotate(
        bill_name_cached=Subquery(ServiceBill.objects.filter(maintenance_id=OuterRef("pk")).values("name")[:1]),
    )
    serializer_class = MaintenanceSerializer
    filter_serializer_class = MaintenanceFilter
    filters = {"branch": "vehicle__branch_id", "branch_active": "vehicle__branch__is_active"}


class MaintenanceDetailAPIView(DetailAPIView):
    queryset = MaintenanceCollectionAPIView.queryset
    serializer_class = MaintenanceSerializer


class ServiceBillAPIView(APIView):
    def get(self, request, identifier):
        bill = get_object_or_404(ServiceBill, maintenance_id=identifier)
        response = FileResponse(BytesIO(bill.data), as_attachment=True, filename=bill.name, content_type=bill.content_type)
        response["Cache-Control"] = "no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
