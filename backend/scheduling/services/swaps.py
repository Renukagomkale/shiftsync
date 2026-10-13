from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import User
from scheduling.models import Shift, SwapRequest

from .conflicts import ensure_can_work, find_conflicts
from .notifications import coworkers_of, describe, managers_of, notify

Status = SwapRequest.Status
ACTIVE = [Status.PENDING_PEER, Status.PENDING_MANAGER]


def lock(swap, allowed):
    locked = SwapRequest.objects.select_for_update().get(pk=swap.pk)
    if locked.status not in allowed:
        raise ValidationError(f"This swap is {locked.get_status_display()}, so that action is not available.")
    return locked


def finish(swap, status):
    swap.status = status
    swap.resolved_at = timezone.now()
    swap.save(update_fields=["status", "resolved_at"])
    return swap


def require_manager(swap, user):
    if user.role != User.Role.MANAGER or user.business_id != swap.shift.business_id:
        raise PermissionDenied("Only a manager of this business can do this.")


def require_eligible_peer(swap, user):
    not_sent_to_user = swap.target_worker_id not in (None, user.id)
    if user.id == swap.requested_by_id or not_sent_to_user or user.business_id != swap.shift.business_id:
        raise PermissionDenied("This swap request was not sent to you.")


@transaction.atomic
def create_swap(requester, shift, target):
    shift = Shift.objects.select_for_update().get(pk=shift.pk)
    if shift.assigned_to_id != requester.id:
        raise PermissionDenied("You can only request a swap for your own shifts.")
    if shift.start <= timezone.now():
        raise ValidationError("This shift has already started.")
    if target is not None and target.id == requester.id:
        raise ValidationError("You cannot swap a shift with yourself.")
    if SwapRequest.objects.filter(shift=shift, status__in=ACTIVE).exists():
        raise ValidationError("This shift already has an open swap request.")
    swap = SwapRequest.objects.create(shift=shift, requested_by=requester, target_worker=target)
    if target is not None:
        notify([target], f"{requester.name} wants to swap {describe(shift)} with you.", swap)
    else:
        notify(coworkers_of(requester), f"{requester.name} is looking for someone to cover {describe(shift)}.", swap)
    return swap


@transaction.atomic
def accept_as_peer(swap, user):
    swap = lock(swap, [Status.PENDING_PEER])
    require_eligible_peer(swap, user)
    conflicts = find_conflicts(user.business, user, swap.shift.start, swap.shift.end)
    if conflicts:
        raise ValidationError([conflict["message"] for conflict in conflicts])
    swap.target_worker = user
    swap.status = Status.PENDING_MANAGER
    swap.save(update_fields=["target_worker", "status"])
    what = describe(swap.shift)
    notify([swap.requested_by], f"{user.name} accepted your swap for {what}. It now needs manager approval.", swap)
    notify(
        managers_of(swap.shift.business_id),
        f"{swap.requested_by.name} and {user.name} want to swap {what}. Approval needed.",
        swap,
    )
    return swap


@transaction.atomic
def decline_as_peer(swap, user):
    swap = lock(swap, [Status.PENDING_PEER])
    if swap.target_worker_id != user.id:
        raise PermissionDenied("Only the coworker this request was sent to can decline it.")
    notify([swap.requested_by], f"{user.name} declined your swap for {describe(swap.shift)}.", swap)
    return finish(swap, Status.REJECTED)


@transaction.atomic
def approve(swap, manager):
    require_manager(swap, manager)
    swap = lock(swap, [Status.PENDING_MANAGER])
    shift = Shift.objects.select_for_update().get(pk=swap.shift_id)
    if shift.assigned_to_id != swap.requested_by_id:
        raise ValidationError("This shift changed after the swap was requested. Reject this request and ask for a new one.")
    ensure_can_work(manager.business, swap.target_worker, shift.start, shift.end, exclude_shift=shift, field=None)
    shift.assigned_to = swap.target_worker
    shift.save(update_fields=["assigned_to"])
    notify(
        [swap.requested_by, swap.target_worker],
        f"Swap approved: {swap.target_worker.name} now has {describe(shift)}.",
        swap,
    )
    return finish(swap, Status.APPROVED)


@transaction.atomic
def reject(swap, manager):
    require_manager(swap, manager)
    swap = lock(swap, [Status.PENDING_MANAGER])
    notify(
        [swap.requested_by, swap.target_worker],
        f"The manager declined the swap for {describe(swap.shift)}. The shift stays with {swap.requested_by.name}.",
        swap,
    )
    return finish(swap, Status.REJECTED)


@transaction.atomic
def cancel(swap, user):
    if swap.requested_by_id != user.id:
        raise PermissionDenied("Only the person who asked for the swap can cancel it.")
    swap = lock(swap, ACTIVE)
    message = f"{user.name} cancelled the swap request for {describe(swap.shift)}."
    notify([swap.target_worker], message, swap)
    if swap.status == Status.PENDING_MANAGER:
        notify(managers_of(swap.shift.business_id), message, swap)
    return finish(swap, Status.CANCELLED)
