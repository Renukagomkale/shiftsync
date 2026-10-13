from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from accounts.models import Business, User

MONDAY = (2026, 10, 12)


def at(days, hours, minutes=0, tz="UTC"):
    start_of_week = datetime(*MONDAY, tzinfo=ZoneInfo(tz))
    return start_of_week + timedelta(days=days, hours=hours, minutes=minutes)


def make_business(name="Corner Brew Cafe", **fields):
    return Business.objects.create(name=name, **fields)


def make_user(business, email, role="worker"):
    return User.objects.create_user(
        email=email, password="Sunny-day-42", name=email.split("@")[0].title(), role=role, business=business
    )


def future(days, hours):
    midnight = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight + timedelta(days=days, hours=hours)
