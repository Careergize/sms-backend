from django.urls import path

from .views import BranchCollectionAPIView, BranchDetailAPIView

urlpatterns = [
    path("", BranchCollectionAPIView.as_view()),
    path("<slug:identifier>/", BranchDetailAPIView.as_view()),
]
