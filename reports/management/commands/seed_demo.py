import json
from datetime import date, datetime, time, timedelta
from math import floor
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from attendance.models import Attendance
from branches.models import Branch
from catalog.models import CatalogEntry
from enquiries.models import Enquiry
from instructors.models import Instructor
from lessons.models import Lesson
from reports.models import BranchSnapshot, MonthlyReport
from students.models import Student

SNAPSHOT_DATE = date(2026, 11, 9)
BRANCHES = (
    ("Vanchiyoor", 24, 8, 10, 3),
    ("Peroorkada", 19, 6, 8, 2),
    ("Kulathoor", 17, 5, 7, 1),
    ("Manakkadu", 20, 7, 9, 2),
    ("Njakkal", 15, 5, 6, 2),
)
STUDENTS = (
    ("Ananya Rao", "Vikram Shah", "Meera Das", "Aarav Nair"),
    ("Rahul Das", "Isha Patel", "Kabir Singh", "Sana Joseph"),
    ("Neha Reddy", "Arjun Mehta", "Tara Roy", "Dev Sharma"),
    ("Rohan Iyer", "Maya Joshi", "Aditya Sen", "Kavya Menon"),
    ("Diya Nair", "Nikhil Jain", "Asha Pillai", "Kiran Sethi"),
)
FIRST_NAMES = ("Arun", "Meena", "Karthik", "Divya", "Ravi", "Priya", "Suresh", "Nisha")
LAST_NAMES = ("Kumar", "Rajan", "Mani", "Prasad", "Devi")
FACTORS = (0.84, 0.94, 0.88, 1.08, 1.22, 0.61)


def rounded(number):
    return floor(number + 0.5)


def demo_student_details(index, offset, instructor, paid):
    fee = (5400, 7200, 3500, 4200)[offset]
    return {
        "phone": f"+91 XXXXX X{index + 1:02}{offset + 1:02}",
        "guardian_name": f"Demo contact {index + 1:02}-{offset + 1:02}",
        "guardian_phone": f"+91 XXXXX G{index + 1:02}{offset + 1:02}",
        "instructor": instructor,
        "total_fee": fee,
        "amount_paid": fee if paid else fee // 2,
    }


def seed_students(branch, index, instructor):
    courses = (Student.Course.MANUAL, Student.Course.AUTOMATIC, Student.Course.TWO_WHEELER, Student.Course.REFRESHER)
    statuses = (Student.Status.IN_TRAINING, Student.Status.ENROLLED, Student.Status.IN_TRAINING, Student.Status.COMPLETED)
    students = []
    for offset, name in enumerate(STUDENTS[index]):
        paid = offset == 3 or (index + offset) % 3 == 0
        student, _ = Student.objects.get_or_create(
            code=f"STU-{branch.code}-{offset + 1:02}",
            defaults={
                "branch": branch, "name": name, "course": courses[offset], "status": statuses[offset],
                "payment": Student.Payment.PAID if paid else Student.Payment.UNPAID,
                "enrolled_on": SNAPSHOT_DATE - timedelta(days=offset * 7),
                **demo_student_details(index, offset, instructor, paid),
            },
        )
        students.append(student)
    return students


def seed_instructors(branch, index, count):
    instructors = []
    for offset in range(count):
        code = f"INS-{branch.code}-{offset + 1:02}"
        instructor, _ = Instructor.objects.get_or_create(
            code=code,
            defaults={
                "branch": branch, "name": f"{FIRST_NAMES[offset]} {LAST_NAMES[index]}",
                "mobile": f"+91 XXXXX X{index + 1:02}{offset + 1:02}",
                "email": f"{code.lower()}@example.com", "address": f"{offset + 12} Demo Lane, {branch.area or branch.name}",
                "experience_years": 3 + offset, "licence_number": f"DEMO-DL-{branch.code}-{offset + 1:02}",
                "licence_valid_until": date(2027 + offset % 3, 6, 15),
                "joined_on": date(2020 + offset % 5, 8, 1),
                "status": Instructor.Status.ON_LEAVE if offset == 3 else Instructor.Status.ACTIVE,
            },
        )
        instructors.append(instructor)
    return instructors


def seed_instructor_attendance(branch, instructors):
    Attendance.objects.bulk_create([
        Attendance(
            branch=branch, instructor=instructor, date=SNAPSHOT_DATE - timedelta(days=offset),
            status=Attendance.Status.ABSENT if (instructor_index + offset) % 7 == 3 else Attendance.Status.PRESENT,
        )
        for instructor_index, instructor in enumerate(instructors)
        for offset in range(8)
    ], ignore_conflicts=True)


def seed_lessons(index, students, instructor):
    for week in (-1, 0, 1):
        for offset in range(3):
            slot = (index * 3 + offset) * 11 % 63
            day = (slot // 9 + week) % 7
            lesson_date = SNAPSHOT_DATE + timedelta(weeks=week, days=day)
            starts_at = timezone.make_aware(datetime.combine(lesson_date, time(hour=8 + slot % 9)))
            attendance = Lesson.Attendance.SCHEDULED
            if lesson_date <= SNAPSHOT_DATE:
                attendance = Lesson.Attendance.ABSENT if (index + offset) % 5 == 0 else Lesson.Attendance.PRESENT
            student = students[(offset + week + 1) % len(students)]
            if not Lesson.objects.filter(student=student, starts_at=starts_at).exists():
                Lesson.objects.get_or_create(
                    instructor=instructor, starts_at=starts_at,
                    defaults={"student": student, "attendance": attendance},
                )


def seed_reports(branch, index, base, instructors, vehicles, admissions_today):
    BranchSnapshot.objects.get_or_create(
        branch=branch, date=SNAPSHOT_DATE,
        defaults={
            "active_students": base * 3, "admissions_today": admissions_today,
            "instructors": instructors, "vehicles": vehicles,
            "training_sessions_today": instructors * 3, "tests_scheduled": vehicles + 1,
        },
    )
    for period, factor in enumerate(FACTORS):
        admissions = rounded(base * factor) + (index + period) % 5
        tests = rounded(admissions * 0.67)
        slots = vehicles * 32
        manual = rounded(admissions * 0.46)
        automatic = rounded(admissions * 0.27)
        two_wheeler = rounded(admissions * 0.17)
        MonthlyReport.objects.get_or_create(
            branch=branch, month=date(2026, 6 + period, 1),
            defaults={
                "admissions": admissions, "enquiries": admissions * 2 + 12 + index,
                "revenue": admissions * (6700 + index * 150) + 9300,
                "expenses": admissions * (3540 + index * 120) + 6100,
                "pending_payments": admissions * (480 + index * 40),
                "completed": rounded(admissions * (0.65 + index * 0.025)),
                "tests_taken": tests, "tests_passed": rounded(tests * (0.76 + index * 0.023)),
                "lessons_delivered": instructors * (28 + (index + period) % 6), "lesson_target": instructors * 35,
                "available_vehicle_slots": slots,
                "booked_vehicle_slots": rounded(slots * (0.69 + index * 0.035 + period * 0.012)),
                "manual": manual, "automatic": automatic, "two_wheeler": two_wheeler,
                "refresher": admissions - manual - automatic - two_wheeler,
            },
        )


class Command(BaseCommand):
    help = "Populate the local CRM with fictional records without overwriting existing records."

    @transaction.atomic
    def handle(self, *args, **options):
        for index, (name, base, instructor_count, vehicles, admissions) in enumerate(BRANCHES):
            branch, _ = Branch.objects.get_or_create(
                code=f"B{index + 1:02}", defaults={"name": name},
            )
            instructors = seed_instructors(branch, index, instructor_count)
            students = seed_students(branch, index, instructors[0])
            seed_lessons(index, students, instructors[0])
            seed_instructor_attendance(branch, instructors)
            seed_reports(branch, index, base, instructor_count, vehicles, admissions)

        catalog_file = Path(__file__).with_name("demo_catalog.json")
        for entry in json.loads(catalog_file.read_text(encoding="utf-8")):
            slug = entry.pop("slug")
            CatalogEntry.objects.get_or_create(slug=slug, defaults=entry)

        for index, name in enumerate(("Asha Demo", "Ravi Demo", "Nisha Demo"), start=1):
            Enquiry.objects.get_or_create(
                email=f"demo-enquiry-{index}@example.com",
                defaults={
                    "name": name, "phone": f"+91 XXXXX X000{index}",
                    "programme": "General enquiry", "message": "Demo enquiry about lesson availability.",
                },
            )
        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
