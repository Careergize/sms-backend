from django.db import models

from instructors.models import Instructor
from students.models import Student


class Lesson(models.Model):
    class Attendance(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="lessons")
    instructor = models.ForeignKey(Instructor, on_delete=models.PROTECT, related_name="lessons")
    starts_at = models.DateTimeField(db_index=True)
    attendance = models.CharField(max_length=12, choices=Attendance, default=Attendance.SCHEDULED)

    class Meta:
        ordering = ("starts_at", "pk")
        constraints = [
            models.UniqueConstraint(fields=("student", "starts_at"), name="unique_student_lesson_slot"),
            models.UniqueConstraint(fields=("instructor", "starts_at"), name="unique_instructor_lesson_slot"),
        ]
