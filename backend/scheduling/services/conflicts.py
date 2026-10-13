from datetime import timedelta
from zoneinfo import ZoneInfo

from rest_framework.exceptions import ValidationError

from accounts.models import User
from scheduling.models import Shift


def hours_between(start, end):
    return (end - start).total_seconds() / 3600


def week_bounds(moment, tz):
    local = moment.astimezone(tz)
    monday = (local - timedelta(days=local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return monday, monday + timedelta(days=7)


def find_conflicts(business, worker, start, end, exclude_shift=None):
    others = Shift.objects.filter(assigned_to=worker)
    if exclude_shift is not None and exclude_shift.pk:
        others = others.exclude(pk=exclude_shift.pk)

    conflicts = []

    if others.filter(start__lt=end, end__gt=start).exists():
        conflicts.append({"code": "overlap", "message": f"{worker.name} already has a shift that overlaps with this time."})

    rest = timedelta(hours=business.min_rest_hours)
    too_close = others.filter(start__lt=end + rest, end__gt=start - rest).exclude(start__lt=end, end__gt=start)
    if rest and too_close.exists():
        conflicts.append(
            {"code": "rest_gap", "message": f"{worker.name} needs at least {business.min_rest_hours} hours of rest between shifts."}
        )

    week_start, week_end = week_bounds(start, ZoneInfo(business.timezone))
    booked = sum(
        hours_between(s, e)
        for s, e in others.filter(start__gte=week_start, start__lt=week_end).values_list("start", "end")
    )
    total = booked + hours_between(start, end)
    if total > business.max_hours_per_week:
        conflicts.append(
            {
                "code": "weekly_hours",
                "message": f"This would bring {worker.name} to {total:g} hours this week. The limit is {business.max_hours_per_week}.",
            }
        )

    return conflicts


def ensure_can_work(business, worker, start, end, exclude_shift=None, field="assigned_to"):
    User.objects.select_for_update().get(pk=worker.pk)
    conflicts = find_conflicts(business, worker, start, end, exclude_shift)
    if conflicts:
        messages = [conflict["message"] for conflict in conflicts]
        raise ValidationError({field: messages} if field else messages)
