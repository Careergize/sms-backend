from django.db.models import Max, Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BranchSnapshot, MonthlyReport
from .serializers import ReportFilters

MONTHLY_FIELDS = (
    "admissions", "enquiries", "revenue", "expenses", "pending_payments", "completed",
    "tests_taken", "tests_passed", "lessons_delivered", "lesson_target",
    "booked_vehicle_slots", "available_vehicle_slots", "manual", "automatic", "two_wheeler", "refresher",
)
SNAPSHOT_FIELDS = (
    "active_students", "admissions_today", "instructors", "vehicles",
    "training_sessions_today", "tests_scheduled",
)


def sums(fields):
    return {field: Sum(field, default=0) for field in fields}


def ratio(value, total):
    return round(100 * value / total, 1) if total else 0


class ReportAPIView(APIView):
    def get(self, request):
        serializer = ReportFilters(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        period = serializer.validated_data["period"]
        branch = serializer.validated_data.get("branch")
        branch_active = serializer.validated_data.get("branch_active")
        reports = MonthlyReport.objects.all()
        if branch_active is not None:
            reports = reports.filter(branch__is_active=branch_active)
        months = list(
            reports.values_list("month", flat=True).order_by("-month").distinct()[:period]
        )
        reports = reports.filter(month__in=months)
        if branch:
            reports = reports.filter(branch_id=branch)
        return Response(self.build_response(reports, branch, period, branch_active))

    def build_response(self, reports, branch, period, branch_active):
        raise NotImplementedError


class DashboardAPIView(ReportAPIView):
    def build_response(self, reports, branch, period, branch_active):
        snapshots = BranchSnapshot.objects.all()
        if branch_active is not None:
            snapshots = snapshots.filter(branch__is_active=branch_active)
        date = snapshots.aggregate(latest=Max("date"))["latest"]
        snapshots = snapshots.filter(date=date)
        if branch:
            snapshots = snapshots.filter(branch_id=branch)
        return {
            "period": period,
            "currency": "INR",
            "totals": reports.aggregate(**sums(MONTHLY_FIELDS)),
            "snapshot": {
                "date": date,
                "branches": snapshots.count(),
                **snapshots.aggregate(**sums(SNAPSHOT_FIELDS)),
            },
        }


class TrendsAPIView(ReportAPIView):
    def build_response(self, reports, branch, period, branch_active):
        return list(reports.values("month").annotate(**sums(MONTHLY_FIELDS)).order_by("month"))


class BranchComparisonAPIView(ReportAPIView):
    def build_response(self, reports, branch, period, branch_active):
        rows = list(reports.values("branch_id", "branch__name", "branch__area")
                    .annotate(**sums(MONTHLY_FIELDS)).order_by("branch_id"))
        for row in rows:
            row["enquiry_conversion_pct"] = ratio(row["admissions"], row["enquiries"])
            row["test_pass_pct"] = ratio(row["tests_passed"], row["tests_taken"])
        return rows


class OperationsAPIView(ReportAPIView):
    def build_response(self, reports, branch, period, branch_active):
        totals = reports.aggregate(**sums(MONTHLY_FIELDS))
        measures = {
            "enquiry_conversion": ("admissions", "enquiries"),
            "training_completion": ("completed", "admissions"),
            "test_pass_rate": ("tests_passed", "tests_taken"),
            "instructor_performance": ("lessons_delivered", "lesson_target"),
            "vehicle_utilisation": ("booked_vehicle_slots", "available_vehicle_slots"),
        }
        return {
            "indicators": {
                name: {"value": totals[value], "total": totals[total], "percent": ratio(totals[value], totals[total])}
                for name, (value, total) in measures.items()
            },
            "course_mix": {key: totals[key] for key in ("manual", "automatic", "two_wheeler", "refresher")},
        }
