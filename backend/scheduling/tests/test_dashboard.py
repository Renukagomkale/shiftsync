from rest_framework.test import APITestCase

from scheduling.models import Shift, SwapRequest

from .base import at, make_business, make_user

WEEK = {"week": "2026-10-14"}


class DashboardTests(APITestCase):
    def setUp(self):
        self.business = make_business(min_rest_hours=0, max_hours_per_week=40)
        self.manager = make_user(self.business, "priya@example.com", "manager")
        self.maya = make_user(self.business, "maya@example.com")
        self.arjun = make_user(self.business, "arjun@example.com")
        self.client.force_authenticate(self.manager)

    def book(self, day, start_hour, end_hour, worker=None, business=None):
        return Shift.objects.create(
            business=business or self.business,
            position="Barista",
            start=at(day, start_hour),
            end=at(day, end_hour),
            assigned_to=worker,
        )

    def summary(self, **params):
        return self.client.get("/api/dashboard/summary/", {**WEEK, **params})

    def test_only_managers_can_see_the_dashboard(self):
        self.client.force_authenticate(self.maya)
        self.assertEqual(self.summary().status_code, 403)

    def test_hours_per_worker_includes_people_with_no_shifts(self):
        self.book(0, 8, 14, self.maya)
        self.book(2, 9, 17, self.maya)
        hours = {row["name"]: row["hours"] for row in self.summary().data["hours_per_worker"]}
        self.assertEqual(hours, {"Arjun": 0, "Maya": 14})

    def test_unassigned_shifts_are_limited_to_the_chosen_week(self):
        self.book(1, 8, 14)
        self.book(7, 8, 14)
        self.book(1, 15, 18, self.maya)
        data = self.summary().data
        self.assertEqual(len(data["unassigned_shifts"]), 1)
        self.assertIsNone(data["unassigned_shifts"][0]["assigned_to"])

    def test_week_boundaries_follow_monday_to_sunday(self):
        self.book(-1, 20, 23)
        self.book(6, 20, 23)
        self.book(7, 0, 4)
        self.assertEqual(len(self.summary().data["unassigned_shifts"]), 1)

    def test_pending_swaps_counts_only_those_waiting_for_the_manager(self):
        shift = self.book(1, 8, 14, self.maya)
        SwapRequest.objects.create(shift=shift, requested_by=self.maya, target_worker=self.arjun, status="pending_manager")
        other = self.book(2, 8, 14, self.maya)
        SwapRequest.objects.create(shift=other, requested_by=self.maya, target_worker=self.arjun, status="pending_peer")
        self.assertEqual(self.summary().data["pending_swaps"], 1)

    def test_other_businesses_are_not_included(self):
        other = make_business(name="Other Shop")
        make_user(other, "stranger@example.com")
        self.book(1, 8, 14, business=other)
        data = self.summary().data
        self.assertEqual(data["unassigned_shifts"], [])
        self.assertEqual(len(data["hours_per_worker"]), 2)

    def test_default_week_and_invalid_week(self):
        self.assertEqual(self.client.get("/api/dashboard/summary/").status_code, 200)
        self.assertEqual(self.summary(week="soon").status_code, 400)
