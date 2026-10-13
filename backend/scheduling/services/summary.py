from collections import defaultdict
from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.utils import timezone

from accounts.models import User
from scheduling.models import Shift, SwapRequest

from .conflicts import hours_between, week_bounds


def build_summary(business, day=None):
    tz = ZoneInfo(business.timezone)
    moment = datetime.combine(day, time.min, tzinfo=tz) if day else timezone.now()
    week_start, week_end = week_bounds(moment, tz)

    week_shifts = Shift.objects.filter(business=business, start__gte=week_start, start__lt=week_end)
    hours = defaultdict(float)
    assigned = week_shifts.filter(assigned_to__isnull=False).values_list("assigned_to_id", "start", "end")
    for worker_id, start, end in assigned:
        hours[worker_id] += hours_between(start, end)

    workers = User.objects.filter(business=business, role=User.Role.WORKER).order_by("name")
    return {
        "week_start": week_start,
        "week_end": week_end,
        "max_hours_per_week": business.max_hours_per_week,
        "unassigned_shifts": week_shifts.filter(assigned_to__isnull=True),
        "hours_per_worker": [
            {"worker_id": worker.id, "name": worker.name, "hours": round(hours[worker.id], 2)} for worker in workers
        ],
        "pending_swaps": SwapRequest.objects.filter(
            shift__business=business, status=SwapRequest.Status.PENDING_MANAGER
        ).count(),
    }
