from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Business, User
from scheduling.models import Shift
from scheduling.services import swaps

PASSWORD = "Demo-pass-2026"
BUSINESS_NAME = "Corner Brew Cafe"
TIMEZONE = "Asia/Kolkata"
MANAGER_EMAIL = "priya@shiftsync.test"

TEAM = [
    ("manager", "Priya Nair", MANAGER_EMAIL),
    ("worker", "Maya Joshi", "maya@shiftsync.test"),
    ("worker", "Arjun Rao", "arjun@shiftsync.test"),
    ("worker", "Sana Khan", "sana@shiftsync.test"),
    ("worker", "Dev Patil", "dev@shiftsync.test"),
]

PATTERN = [
    (0, "Baker", 6, 12, "Arjun"),
    (0, "Barista", 8, 14, "Maya"),
    (0, "Cashier", 12, 18, "Sana"),
    (1, "Barista", 8, 14, None),
    (1, "Floor", 12, 20, "Dev"),
    (1, "Cashier", 14, 20, "Sana"),
    (2, "Baker", 6, 12, "Arjun"),
    (2, "Barista", 12, 18, "Maya"),
    (3, "Barista", 8, 14, "Maya"),
    (3, "Cashier", 8, 14, None),
    (3, "Floor", 14, 20, "Dev"),
    (4, "Baker", 6, 12, "Arjun"),
    (4, "Barista", 12, 20, "Maya"),
    (4, "Cashier", 12, 20, "Sana"),
    (5, "Barista", 9, 15, "Dev"),
    (5, "Floor", 9, 17, None),
    (6, "Barista", 9, 15, "Maya"),
]


class Command(BaseCommand):
    help = "Create a demo business with a team, two weeks of shifts and a few swap requests."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete the existing demo business first.")

    @transaction.atomic
    def handle(self, *args, **options):
        existing = User.objects.filter(email=MANAGER_EMAIL).select_related("business").first()
        if existing and not options["reset"]:
            self.stdout.write("Demo data already exists. Run with --reset to rebuild it.")
            return
        if existing:
            Shift.objects.filter(business=existing.business).delete()
            User.objects.filter(business=existing.business).delete()
            existing.business.delete()

        business = Business.objects.create(
            name=BUSINESS_NAME, timezone=TIMEZONE, min_rest_hours=10, max_hours_per_week=40
        )
        people = {
            name.split()[0]: User.objects.create_user(
                email=email, password=PASSWORD, name=name, role=role, business=business
            )
            for role, name, email in TEAM
        }

        tz = ZoneInfo(TIMEZONE)
        today = timezone.now().astimezone(tz).date()
        monday = today - timedelta(days=today.weekday())
        shifts = {}
        for week in (0, 1):
            for day, position, start, end, who in PATTERN:
                date = monday + timedelta(days=7 * week + day)
                shifts[(week, day, position)] = Shift.objects.create(
                    business=business,
                    position=position,
                    start=datetime.combine(date, time(start), tzinfo=tz),
                    end=datetime.combine(date, time(end), tzinfo=tz),
                    assigned_to=people.get(who),
                    created_by=people["Priya"],
                )

        swaps.create_swap(people["Dev"], shifts[(1, 3, "Floor")], people["Sana"])
        waiting = swaps.create_swap(people["Maya"], shifts[(1, 6, "Barista")], people["Arjun"])
        swaps.accept_as_peer(waiting, people["Arjun"])
        swaps.create_swap(people["Sana"], shifts[(1, 0, "Cashier")], None)

        self.stdout.write(self.style.SUCCESS(f"Created {BUSINESS_NAME} with {len(shifts)} shifts and 3 swap requests."))
        self.stdout.write(f"Manager login: {MANAGER_EMAIL} / {PASSWORD}")
        self.stdout.write(f"Worker logins: maya, arjun, sana, dev @shiftsync.test / {PASSWORD}")
