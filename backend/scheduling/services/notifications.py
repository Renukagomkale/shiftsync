from zoneinfo import ZoneInfo

from accounts.models import User
from scheduling.models import Notification


def describe(shift):
    tz = ZoneInfo(shift.business.timezone)
    start = shift.start.astimezone(tz)
    end = shift.end.astimezone(tz)
    return f"{start:%a %d %b}, {start:%H:%M} to {end:%H:%M} ({shift.position})"


def notify(users, message, swap=None):
    Notification.objects.bulk_create([Notification(user=user, message=message, swap=swap) for user in users if user])


def managers_of(business_id):
    return User.objects.filter(business_id=business_id, role=User.Role.MANAGER)


def coworkers_of(user):
    return User.objects.filter(business_id=user.business_id, role=User.Role.WORKER).exclude(pk=user.pk)
