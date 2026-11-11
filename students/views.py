from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.response import Response

from common.views import CollectionAPIView, DetailAPIView

from .models import Student
from .serializers import StudentDetailSerializer, StudentFilters, StudentSerializer


class StudentCollectionAPIView(CollectionAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    filter_serializer_class = StudentFilters
    filters = {"branch_active": "branch__is_active"}


class StudentDetailAPIView(DetailAPIView):
    queryset = Student.objects.select_related("branch", "instructor")
    serializer_class = StudentDetailSerializer

    def delete(self, request, identifier):
        if request.query_params.get("delete_lessons") != "1":
            return super().delete(request, identifier)
        try:
            with transaction.atomic():
                student = self.get_object(identifier)
                student.lessons.all().delete()
                student.delete()
        except IntegrityError:
            return Response({"detail": "The student has linked records."}, status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)
