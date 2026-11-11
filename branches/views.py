from common.views import CollectionAPIView, DetailAPIView

from .models import Branch
from .serializers import BranchFilters, BranchSerializer


class BranchCollectionAPIView(CollectionAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    filter_serializer_class = BranchFilters


class BranchDetailAPIView(DetailAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    lookup_field = "code"
