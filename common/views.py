from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView


class ResourceAPIView(APIView):
    queryset = None
    serializer_class = None
    lookup_field = "pk"

    def get_object(self, identifier):
        return get_object_or_404(self.queryset.all(), **{self.lookup_field: identifier})

    def save(self, serializer):
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError as exc:
            raise ValidationError("The record conflicts with an existing record.") from exc


class CollectionAPIView(ResourceAPIView):
    filter_serializer_class = None
    filters = {}

    def get(self, request):
        queryset = self.queryset.all()
        if self.filter_serializer_class:
            params = self.filter_serializer_class(data=request.query_params)
            params.is_valid(raise_exception=True)
            queryset = queryset.filter(**{
                self.filters.get(key, key): value
                for key, value in params.validated_data.items()
            })
        return Response(self.serializer_class(queryset, many=True).data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        self.save(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DetailAPIView(ResourceAPIView):
    def get(self, request, identifier):
        return Response(self.serializer_class(self.get_object(identifier)).data)

    def put(self, request, identifier):
        return self.update(request, identifier, partial=False)

    def patch(self, request, identifier):
        return self.update(request, identifier, partial=True)

    def update(self, request, identifier, partial):
        serializer = self.serializer_class(
            self.get_object(identifier), data=request.data, partial=partial,
        )
        self.save(serializer)
        return Response(serializer.data)

    def delete(self, request, identifier):
        try:
            with transaction.atomic():
                self.get_object(identifier).delete()
        except IntegrityError:
            return Response(
                {"detail": "Other records reference this record."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
