from django.contrib.auth import authenticate
from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(trim_whitespace=False, write_only=True)


class LoginAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        credentials = LoginSerializer(data=request.data)
        credentials.is_valid(raise_exception=True)
        user = authenticate(request=request, **credentials.validated_data)
        if user is None or not user.is_staff:
            return Response({"detail": "Invalid staff credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "username": user.get_username()})


class LogoutAPIView(APIView):
    def post(self, request):
        request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileAPIView(APIView):
    def get(self, request):
        return Response({"username": request.user.get_username(), "is_staff": request.user.is_staff})
