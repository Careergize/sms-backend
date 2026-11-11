from django.db import models
from django.db.models import Q

from branches.models import Branch
from instructors.models import Instructor
from students.models import Student


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=8, choices=Status)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(student__isnull=False, instructor__isnull=True) | Q(student__isnull=True, instructor__isnull=False),
                name="attendance_exactly_one_person",
            ),
            models.UniqueConstraint(fields=("student", "date"), name="unique_student_attendance_date"),
            models.UniqueConstraint(fields=("instructor", "date"), name="unique_instructor_attendance_date"),
        ]
