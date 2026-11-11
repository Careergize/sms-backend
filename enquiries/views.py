from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from common.views import CollectionAPIView, DetailAPIView

from .models import Enquiry
from .serializers import EnquiryFilters, EnquirySerializer, PublicEnquirySerializer


class EnquiryCollectionAPIView(CollectionAPIView):
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySerializer
    filter_serializer_class = EnquiryFilters

    def get_permissions(self):
        permission = AllowAny if self.request.method in ("POST",) else IsAdminUser
        return [permission()]

    def get_throttles(self):
        return [ScopedRateThrottle()] if self.request.method == "POST" else []

    throttle_scope = "enquiry"

    def post(self, request):
        serializer = PublicEnquirySerializer(data=request.data)
        self.save(serializer)
        return Response({"id": serializer.instance.pk}, status=status.HTTP_201_CREATED)


class EnquiryDetailAPIView(DetailAPIView):
    queryset = Enquiry.objects.all()
    serializer_class = EnquirySerializer
