from django.urls import path

from .views import BranchComparisonAPIView, DashboardAPIView, OperationsAPIView, TrendsAPIView

urlpatterns = [
    path("dashboard/", DashboardAPIView.as_view()),
    path("reports/", TrendsAPIView.as_view()),
    path("reports/branch-comparison/", BranchComparisonAPIView.as_view()),
    path("operations/", OperationsAPIView.as_view()),
]
