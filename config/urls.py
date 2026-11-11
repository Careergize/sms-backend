from django.urls import include, path

from reports.assistant_pdf import AssistantPdfAPIView

urlpatterns = [
    path("api/auth/", include("accounts.urls")),
    path("api/branches/", include("branches.urls")),
    path("api/catalog/", include("catalog.urls")),
    path("api/students/", include("students.urls")),
    path("api/instructors/", include("instructors.urls")),
    path("api/lessons/", include("lessons.urls")),
    path("api/attendance/", include("attendance.urls")),
    path("api/vehicles/", include("vehicles.urls")),
    path("api/assistant/pdf/", AssistantPdfAPIView.as_view()),
    path("api/enquiries/", include("enquiries.urls")),
    path("api/", include("reports.urls")),
]
