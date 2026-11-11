from django.urls import path

from .views import EnquiryCollectionAPIView, EnquiryDetailAPIView

urlpatterns = [
    path("", EnquiryCollectionAPIView.as_view()),
    path("<int:identifier>/", EnquiryDetailAPIView.as_view()),
]
