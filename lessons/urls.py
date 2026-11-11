from django.urls import path

from .views import LessonCollectionAPIView, LessonDetailAPIView

urlpatterns = [
    path("", LessonCollectionAPIView.as_view()),
    path("<int:identifier>/", LessonDetailAPIView.as_view()),
]
