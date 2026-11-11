from django.db import models


class CatalogEntry(models.Model):
    class Kind(models.TextChoices):
        PROGRAMME = "programme", "Programme"
        SERVICE = "service", "Service"
        EXTRA = "extra", "Extra"
        ARTICLE = "article", "Article"
        FAQ = "faq", "FAQ"

    slug = models.SlugField(primary_key=True)
    kind = models.CharField(max_length=12, choices=Kind)
    name = models.CharField(max_length=160)
    label = models.CharField(max_length=120, blank=True)
    summary = models.TextField()
    skills = models.JSONField(default=list, blank=True)
    body = models.JSONField(default=list, blank=True)
    fee = models.PositiveIntegerField(null=True, blank=True)
    hours = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ("kind", "slug")
