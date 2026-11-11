from common.views import CollectionAPIView, DetailAPIView

from .models import Lesson
from .serializers import LessonFilters, LessonSerializer


class LessonCollectionAPIView(CollectionAPIView):
    queryset = Lesson.objects.select_related("student", "instructor", "vehicle_reservation__vehicle")
    serializer_class = LessonSerializer
    filter_serializer_class = LessonFilters
    filters = {
        "branch": "student__branch_id", "branch_active": "student__branch__is_active",
        "date_from": "starts_at__date__gte", "date_to": "starts_at__date__lte",
    }


class LessonDetailAPIView(DetailAPIView):
    queryset = LessonCollectionAPIView.queryset
    serializer_class = LessonSerializer
