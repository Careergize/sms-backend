from django.db import models

from branches.models import Branch


class Instructor(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ON_LEAVE = "on-leave", "On leave"
        INACTIVE = "inactive", "Inactive"

    code = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=120)
    mobile = models.CharField(max_length=32)
    email = models.EmailField()
    address = models.TextField()
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="instructors")
    experience_years = models.PositiveSmallIntegerField()
    licence_number = models.CharField(max_length=40, unique=True)
    licence_valid_until = models.DateField()
    joined_on = models.DateField()
    status = models.CharField(max_length=12, choices=Status, default=Status.ACTIVE)

    class Meta:
        ordering = ("code",)
