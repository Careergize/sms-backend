from django.urls import path

from .views import LoginAPIView, LogoutAPIView, ProfileAPIView

urlpatterns = [
    path("login/", LoginAPIView.as_view()),
    path("logout/", LogoutAPIView.as_view()),
    path("me/", ProfileAPIView.as_view()),
]
