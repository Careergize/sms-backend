# SMS Motor Driving School API

Django REST Framework backend using `APIView` and SQLite. Use Python 3.10–3.14.

## Run locally

From the workspace root in PowerShell:

```powershell
cd Backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

The server listens on `http://127.0.0.1:8000`. On a fresh database, the seed command adds five branches, 20 students, 31 instructors, 45 lessons, 30 monthly reports, branch snapshots, instructor attendance, public catalogue content, and three sample enquiries. The calendar includes the weeks before, during, and after 9 November 2026. The seed command can be run again without duplicating its records or overwriting edits. Use the staff account created by `createsuperuser`.

## Endpoints

| Endpoint | Methods and purpose |
| --- | --- |
| `/api/auth/login/` | POST username and password to get a token |
| `/api/auth/me/` | GET the authenticated staff profile |
| `/api/auth/logout/` | POST to revoke the staff token |
| `/api/branches/` | GET, POST branches |
| `/api/students/` | GET, POST students. Filters include `branch`, `status`, and `payment` |
| `/api/instructors/` | GET, POST instructors. Filters include `branch` and `status` |
| `/api/lessons/` | GET, POST lessons. Filters include `branch`, `attendance`, `date_from`, and `date_to` |
| `/api/attendance/` | GET daily or monthly attendance by branch and role. POST to mark a person present or absent |
| `/api/vehicles/` | Fleet records and branch filters |
| `/api/vehicles/assignments/` | Instructor assignments, handover condition and returns |
| `/api/vehicles/reservations/` | Time-based reservations, lesson links, blocks, tests, usage, and vehicle moves |
| `/api/vehicles/maintenance/` | Service and repair records, costs, due dates and kilometre readings, and service bills |
| `/api/vehicles/fuel/` | Fuel entries and expense totals grouped by branch, vehicle, and instructor |
| `/api/enquiries/` | Public POST to submit an enquiry. Staff GET to list enquiries and filter by `status` |
| `/api/catalog/` | Public GET catalogue, filterable by `kind`. Staff POST to create entries |
| `/api/dashboard/` | GET period totals and latest snapshot |
| `/api/reports/` | GET monthly trends |
| `/api/reports/branch-comparison/` | GET branch totals and rates |
| `/api/operations/` | GET performance indicators and course mix |

Branch, student, instructor, lesson, enquiry, and catalogue detail URLs accept GET, PUT, PATCH, and DELETE. Append the branch code, catalogue slug, or numeric record ID to the collection URL, followed by a slash. Catalogue detail reads are public. Staff requests use the header `Authorization: Token <token>`.

Student details include guardian contact information, assigned instructor, lesson history, and fees. Set `total_fee` and `amount_paid` together to calculate `pending_amount` and payment status. To delete a student and their linked lessons together, pass `delete_lessons=1` on the student DELETE request. The portal asks for confirmation before doing this.

Attendance GET accepts `kind=students` or `instructors`, `period=day` or `month`, an optional `branch`, and a `date` in `YYYY-MM-DD`. Attendance POST accepts `kind`, a numeric `person` ID, `date`, and `status` (`present` or `absent`). For students, a daily mark takes precedence over lesson attendance. Dates use Asia/Kolkata.

The dashboard uses `is_active=true` on the branch list and `branch_active=true` on branch-scoped records and reports. Omit these parameters to include archived branch records in API responses.

Run `python manage.py seed_vehicle_demo` after `seed_demo` to add example fleet records. Reservation times use Asia/Kolkata in the portal. The reservation endpoint rejects overlapping time ranges for the same vehicle. An existing lesson provides the start time and instructor. To create a lesson and reserve a vehicle in one request, send `purpose=lesson`, `new_student`, `instructor`, and `starts_at`. A reservation can be moved to another vehicle with a `reassignment_reason`. Removing a reservation releases the vehicle and keeps its linked lesson.

Upload a service bill using multipart field `bill` on a maintenance POST or PATCH. The protected download endpoint is `/api/vehicles/maintenance/<id>/bill/`. Bills are limited to 5 MB and accept PDF, PNG, or JPEG. Use the maintenance record's **Block time** action to reserve an unavailable period.

Fuel GET accepts `branch`, `branch_active`, `vehicle`, `instructor`, `date_from`, and `date_to`. It returns an entry log and grouped totals for the selected records. For each fill, expense is litres multiplied by price per litre, rounded to two decimal places. Efficiency appears at a full fill once a previous full fill exists for the vehicle. It includes intervening partial fills even if a date filter hides them.

Run `python manage.py seed_fuel_demo` after `seed_vehicle_demo` to add example full and partial fills to demo vehicles with empty fuel logs.

Use branch codes such as `B01` for branch filters and foreign keys. Use `period=1`, `3`, or `6` for the dashboard and reporting endpoints. Reports use separate demo snapshots and monthly records. They do not recalculate from directory edits. Lessons last 60 minutes and start on the hour in Asia/Kolkata. Date filters are inclusive and use `YYYY-MM-DD`.

For example, list the scheduled lessons for Branch 1 in the demo week:

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/auth/login/ -ContentType application/json -Body (@{username='your-staff-username'; password=(Read-Host 'Staff password' -MaskInput)} | ConvertTo-Json)
Invoke-RestMethod 'http://127.0.0.1:8000/api/lessons/?branch=B01&attendance=scheduled&date_from=2026-11-09&date_to=2026-11-15' -Headers @{Authorization="Token $($login.token)"}
```

## Connect the public enquiry form

The [local frontend](../sms-driving-school/README.md) connects to Django on port 8000. The public enquiry form sends `name`, `phone`, `email`, `programme`, and `message`. Staff can review submissions on the portal's **Enquiries** tab.

Local ports 4173 and 5173 are allowed by default. Configure `SMS_CORS_ORIGINS` as a comma-separated list for a different frontend origin. For deployment, set `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, and `DJANGO_ALLOWED_HOSTS`, and serve the API over HTTPS.
