from django.db import models

from branches.models import Branch
from instructors.models import Instructor


class Student(models.Model):
    class Course(models.TextChoices):
        MANUAL = "manual", "Manual car"
        AUTOMATIC = "automatic", "Automatic car"
        TWO_WHEELER = "two-wheeler", "Two-wheeler"
        REFRESHER = "refresher", "Refresher"

    class Status(models.TextChoices):
        ENROLLED = "enrolled", "Enrolled"
        IN_TRAINING = "in-training", "In training"
        COMPLETED = "completed", "Completed"

    class Payment(models.TextChoices):
        PAID = "paid", "Paid"
        UNPAID = "unpaid", "Unpaid"

    code = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=120)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="students")
    course = models.CharField(max_length=16, choices=Course)
    status = models.CharField(max_length=16, choices=Status, default=Status.ENROLLED)
    payment = models.CharField(max_length=8, choices=Payment, default=Payment.UNPAID)
    enrolled_on = models.DateField()
    phone = models.CharField(max_length=32, blank=True)
    guardian_name = models.CharField(max_length=120, blank=True)
    guardian_phone = models.CharField(max_length=32, blank=True)
    instructor = models.ForeignKey(
        Instructor, on_delete=models.SET_NULL, related_name="assigned_students", null=True, blank=True,
    )
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ("code",)
