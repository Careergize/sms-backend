from django.urls import path

from .fuel import FuelCollectionAPIView, FuelDetailAPIView

from .views import (
    AssignmentCollectionAPIView, AssignmentDetailAPIView, MaintenanceCollectionAPIView, MaintenanceDetailAPIView,
    ReservationCollectionAPIView, ReservationDetailAPIView, ServiceBillAPIView, VehicleCollectionAPIView, VehicleDetailAPIView,
)

urlpatterns = [
    path("", VehicleCollectionAPIView.as_view()),
    path("<int:identifier>/", VehicleDetailAPIView.as_view()),
    path("assignments/", AssignmentCollectionAPIView.as_view()),
    path("assignments/<int:identifier>/", AssignmentDetailAPIView.as_view()),
    path("reservations/", ReservationCollectionAPIView.as_view()),
    path("reservations/<int:identifier>/", ReservationDetailAPIView.as_view()),
    path("maintenance/", MaintenanceCollectionAPIView.as_view()),
    path("maintenance/<int:identifier>/", MaintenanceDetailAPIView.as_view()),
    path("maintenance/<int:identifier>/bill/", ServiceBillAPIView.as_view()),
    path("fuel/", FuelCollectionAPIView.as_view()),
    path("fuel/<int:identifier>/", FuelDetailAPIView.as_view()),
]
