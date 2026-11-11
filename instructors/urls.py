from django.urls import path

from .views import InstructorCollectionAPIView, InstructorDetailAPIView

urlpatterns = [
    path("", InstructorCollectionAPIView.as_view()),
    path("<int:identifier>/", InstructorDetailAPIView.as_view()),
]
