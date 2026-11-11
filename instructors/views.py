from common.views import CollectionAPIView, DetailAPIView

from .models import Instructor
from .serializers import InstructorFilters, InstructorSerializer


class InstructorCollectionAPIView(CollectionAPIView):
    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer
    filter_serializer_class = InstructorFilters
    filters = {"branch_active": "branch__is_active"}


class InstructorDetailAPIView(DetailAPIView):
    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer
