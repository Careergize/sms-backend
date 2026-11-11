from django.urls import path

from .views import StudentCollectionAPIView, StudentDetailAPIView

urlpatterns = [
    path("", StudentCollectionAPIView.as_view()),
    path("<int:identifier>/", StudentDetailAPIView.as_view()),
]
