from django.db import models

from branches.models import Branch


class MonthlyReport(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    month = models.DateField()
    admissions = models.PositiveIntegerField()
    enquiries = models.PositiveIntegerField()
    revenue = models.PositiveIntegerField()
    expenses = models.PositiveIntegerField()
    pending_payments = models.PositiveIntegerField()
    completed = models.PositiveIntegerField()
    tests_taken = models.PositiveIntegerField()
    tests_passed = models.PositiveIntegerField()
    lessons_delivered = models.PositiveIntegerField()
    lesson_target = models.PositiveIntegerField()
    booked_vehicle_slots = models.PositiveIntegerField()
    available_vehicle_slots = models.PositiveIntegerField()
    manual = models.PositiveIntegerField()
    automatic = models.PositiveIntegerField()
    two_wheeler = models.PositiveIntegerField()
    refresher = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("branch", "month"), name="unique_branch_report_month"),
        ]


class BranchSnapshot(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    date = models.DateField()
    active_students = models.PositiveIntegerField()
    admissions_today = models.PositiveIntegerField()
    instructors = models.PositiveIntegerField()
    vehicles = models.PositiveIntegerField()
    training_sessions_today = models.PositiveIntegerField()
    tests_scheduled = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("branch", "date"), name="unique_branch_snapshot_date"),
        ]
