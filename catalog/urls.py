from django.urls import path

from .views import CatalogEntryCollectionAPIView, CatalogEntryDetailAPIView

urlpatterns = [
    path("", CatalogEntryCollectionAPIView.as_view()),
    path("<slug:identifier>/", CatalogEntryDetailAPIView.as_view()),
]
