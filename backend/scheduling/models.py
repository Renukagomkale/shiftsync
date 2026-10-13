from django.conf import settings
from django.db import models


class Shift(models.Model):
    business = models.ForeignKey("accounts.Business", on_delete=models.CASCADE, related_name="shifts")
    position = models.CharField(max_length=60)
    start = models.DateTimeField()
    end = models.DateTimeField()
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="shifts"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    notes = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start", "id"]
        indexes = [models.Index(fields=["business", "start"])]
        constraints = [
            models.CheckConstraint(condition=models.Q(end__gt=models.F("start")), name="shift_end_after_start"),
        ]

    def __str__(self):
        return f"{self.position} {self.start:%Y-%m-%d %H:%M}"


class SwapRequest(models.Model):
    class Status(models.TextChoices):
        PENDING_PEER = "pending_peer", "waiting for a coworker"
        PENDING_MANAGER = "pending_manager", "waiting for the manager"
        APPROVED = "approved", "approved"
        REJECTED = "rejected", "declined"
        CANCELLED = "cancelled", "cancelled"

    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name="swaps")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="swap_requests")
    target_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="incoming_swaps"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_PEER)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["shift"],
                condition=models.Q(status__in=["pending_peer", "pending_manager"]),
                name="one_active_swap_per_shift",
            ),
        ]

    def __str__(self):
        return f"Swap {self.pk} ({self.status})"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    swap = models.ForeignKey(SwapRequest, null=True, blank=True, on_delete=models.CASCADE, related_name="+")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.user_id}: {self.message[:40]}"
