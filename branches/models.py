from django.db import models


class Branch(models.Model):
    code = models.SlugField(max_length=16, primary_key=True)
    name = models.CharField(max_length=100)
    area = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("code",)
