from django.urls import path

from .views import AttendanceAPIView

urlpatterns = [path("", AttendanceAPIView.as_view())]
