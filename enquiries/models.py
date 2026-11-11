from django.db import models


class Enquiry(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        CLOSED = "closed", "Closed"

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    email = models.EmailField(blank=True)
    programme = models.CharField(max_length=160, default="General enquiry")
    message = models.TextField(max_length=2000, blank=True)
    status = models.CharField(max_length=12, choices=Status, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-pk")
