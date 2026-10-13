from django.contrib import admin

from .models import Notification, Shift, SwapRequest


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ["position", "start", "end", "assigned_to", "business"]
    list_filter = ["business", "position"]


@admin.register(SwapRequest)
class SwapRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "shift", "requested_by", "target_worker", "status", "created_at"]
    list_filter = ["status"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "message", "is_read", "created_at"]
