from calendar import monthrange
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from branches.models import Branch
from instructors.models import Instructor
from lessons.models import Lesson
from students.models import Student

from .models import Attendance
from .serializers import AttendanceMark, AttendanceQuery

PEOPLE = {
    "students": (Student, "student", "enrolled_on"),
    "instructors": (Instructor, "instructor", "joined_on"),
}


def lesson_marks(person_ids, start, end):
    lessons = Lesson.objects.filter(
        student_id__in=person_ids,
        starts_at__date__range=(start, end),
        attendance__in=Attendance.Status.values,
    ).values_list("student_id", "starts_at", "attendance")
    marks = {}
    for person_id, starts_at, status in lessons:
        key = (person_id, timezone.localdate(starts_at))
        if status == Attendance.Status.PRESENT or key not in marks:
            marks[key] = status
    return marks


class AttendanceAPIView(APIView):
    def get(self, request):
        query = AttendanceQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        filters = query.validated_data
        selected_date = filters["date"]
        branch = filters.get("branch")
        branch_active = filters.get("branch_active")
        model, role, joined_field = PEOPLE[filters["kind"]]
        role_id = f"{role}_id"

        start = end = selected_date
        if filters["period"] == "month":
            start = selected_date.replace(day=1)
            end = selected_date.replace(day=monthrange(selected_date.year, selected_date.month)[1])
        days = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]

        entries = Attendance.objects.filter(date__range=(start, end), **{f"{role}__isnull": False})
        people = model.objects.filter(**{f"{joined_field}__lte": end})
        if branch_active is not None:
            allowed_branches = set(Branch.objects.filter(is_active=branch_active).values_list("pk", flat=True))
            marked_people = entries.filter(branch_id__in=allowed_branches).values(role_id)
            people = people.filter(branch_id__in=allowed_branches) | people.filter(pk__in=marked_people)
        else:
            allowed_branches = None
        if branch:
            recorded_people = entries.filter(branch_id=branch).values(role_id)
            people = (people.filter(branch_id=branch) | people.filter(pk__in=recorded_people))
        people = list(people.select_related("branch").order_by("branch_id", "name", "pk"))
        ids = [person.pk for person in people]
        recorded = {
            (person_id, day): (branch_id, status)
            for person_id, day, branch_id, status in entries.filter(**{f"{role_id}__in": ids})
            .values_list(role_id, "date", "branch_id", "status")
        }
        inferred = lesson_marks(ids, start, end) if role == "student" else {}

        rows = []
        for person in people:
            marks = {}
            branches = {}
            for day in days:
                if day < getattr(person, joined_field):
                    continue
                current_branch, status = recorded.get(
                    (person.pk, day), (person.branch_id, inferred.get((person.pk, day))),
                )
                if (not branch or current_branch == branch) and (
                    allowed_branches is None or current_branch in allowed_branches
                ):
                    branches[day.isoformat()] = current_branch
                    if status is not None:
                        marks[day.isoformat()] = status
            if branches:
                rows.append({
                    "id": person.pk, "code": person.code, "name": person.name,
                    "branch": branches.get(selected_date.isoformat(), next(iter(branches.values()))),
                    "marks": marks,
                })
        return Response({"date": selected_date, "today": timezone.localdate(), "days": days, "rows": rows})

    def post(self, request):
        mark = AttendanceMark(data=request.data)
        mark.is_valid(raise_exception=True)
        values = mark.validated_data
        model, role, joined_field = PEOPLE[values["kind"]]
        person = get_object_or_404(model, pk=values["person"])
        if values["date"] < getattr(person, joined_field):
            raise ValidationError({"date": "Attendance cannot be marked before the joining date."})
        record, _ = Attendance.objects.update_or_create(
            **{role: person}, date=values["date"],
            defaults={"status": values["status"]},
            create_defaults={"branch_id": person.branch_id, "status": values["status"]},
        )
        return Response({"date": record.date, "status": record.status})
