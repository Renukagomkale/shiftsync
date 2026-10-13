from django.urls import path
from rest_framework.routers import SimpleRouter

from .dashboard_views import DashboardSummaryView
from .notification_views import NotificationViewSet
from .swap_views import SwapViewSet
from .views import ShiftViewSet

router = SimpleRouter()
router.register("shifts", ShiftViewSet, basename="shift")
router.register("swaps", SwapViewSet, basename="swap")
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = router.urls + [
    path("dashboard/summary/", DashboardSummaryView.as_view()),
]
