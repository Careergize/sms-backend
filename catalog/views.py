from rest_framework.permissions import AllowAny, IsAdminUser

from common.views import CollectionAPIView, DetailAPIView

from .models import CatalogEntry
from .serializers import CatalogEntryFilters, CatalogEntrySerializer


class CatalogEntryCollectionAPIView(CollectionAPIView):
    queryset = CatalogEntry.objects.all()
    serializer_class = CatalogEntrySerializer
    filter_serializer_class = CatalogEntryFilters

    def get_permissions(self):
        permission = AllowAny if self.request.method in ("GET", "HEAD", "OPTIONS") else IsAdminUser
        return [permission()]


class CatalogEntryDetailAPIView(DetailAPIView):
    queryset = CatalogEntry.objects.all()
    serializer_class = CatalogEntrySerializer
    lookup_field = "slug"

    def get_permissions(self):
        permission = AllowAny if self.request.method in ("GET", "HEAD", "OPTIONS") else IsAdminUser
        return [permission()]
