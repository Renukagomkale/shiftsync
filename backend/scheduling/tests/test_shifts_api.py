from rest_framework.test import APITestCase

from scheduling.models import Shift

from .base import at, make_business, make_user


class ShiftApiTests(APITestCase):
    def setUp(self):
        self.business = make_business(min_rest_hours=10, max_hours_per_week=40)
        self.manager = make_user(self.business, "priya@example.com", "manager")
        self.worker = make_user(self.business, "maya@example.com")
        self.client.force_authenticate(self.manager)

    def payload(self, **overrides):
        data = {
            "position": "Barista",
            "start": at(0, 8).isoformat(),
            "end": at(0, 14).isoformat(),
            "assigned_to": self.worker.id,
        }
        data.update(overrides)
        return data

    def create(self, **overrides):
        return self.client.post("/api/shifts/", self.payload(**overrides))

    def test_manager_creates_assigned_shift(self):
        response = self.create()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["assigned_to_name"], self.worker.name)
        self.assertEqual(Shift.objects.get().created_by, self.manager)

    def test_worker_cannot_write_but_can_read(self):
        self.create()
        self.client.force_authenticate(self.worker)
        self.assertEqual(self.create().status_code, 403)
        self.assertEqual(self.client.get("/api/shifts/").data["count"], 1)

    def test_user_without_a_business_is_blocked(self):
        self.client.force_authenticate(make_user(None, "lonely@example.com"))
        self.assertEqual(self.client.get("/api/shifts/").status_code, 403)

    def test_overlapping_assignment_is_rejected(self):
        self.create()
        response = self.create(start=at(0, 12).isoformat(), end=at(0, 18).isoformat())
        self.assertEqual(response.status_code, 400)
        self.assertIn("assigned_to", response.data["errors"])

    def test_open_shifts_skip_conflict_checks(self):
        self.assertEqual(self.create(assigned_to=None).status_code, 201)
        self.assertEqual(self.create(assigned_to=None).status_code, 201)

    def test_end_must_be_after_start(self):
        response = self.create(end=at(0, 6).isoformat())
        self.assertEqual(response.status_code, 400)
        self.assertIn("end", response.data["errors"])

    def test_cannot_assign_someone_from_another_business(self):
        outsider = make_user(make_business(name="Other Shop"), "outsider@example.com")
        self.assertEqual(self.create(assigned_to=outsider.id).status_code, 400)

    def test_other_business_shifts_are_hidden(self):
        other = make_business(name="Other Shop")
        shift = Shift.objects.create(business=other, position="Floor", start=at(0, 9), end=at(0, 12))
        self.assertEqual(self.client.get("/api/shifts/").data["count"], 0)
        self.assertEqual(self.client.get(f"/api/shifts/{shift.id}/").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/shifts/{shift.id}/").status_code, 404)

    def test_list_filters_by_date_range(self):
        self.create(assigned_to=None)
        self.create(assigned_to=None, start=at(3, 8).isoformat(), end=at(3, 14).isoformat())
        response = self.client.get("/api/shifts/", {"from": at(2, 0).isoformat(), "to": at(7, 0).isoformat()})
        self.assertEqual(response.data["count"], 1)

    def test_invalid_date_filter_is_rejected(self):
        self.assertEqual(self.client.get("/api/shifts/", {"from": "tomorrow"}).status_code, 400)

    def test_mine_returns_only_own_shifts(self):
        self.create()
        self.create(assigned_to=None, start=at(1, 8).isoformat(), end=at(1, 14).isoformat())
        self.client.force_authenticate(self.worker)
        response = self.client.get("/api/shifts/mine/")
        self.assertEqual(response.data["count"], 1)

    def test_moving_a_shift_into_a_conflict_is_rejected(self):
        self.create()
        second = self.create(start=at(1, 8).isoformat(), end=at(1, 14).isoformat()).data["id"]
        response = self.client.patch(
            f"/api/shifts/{second}/", {"start": at(0, 12).isoformat(), "end": at(0, 18).isoformat()}
        )
        self.assertEqual(response.status_code, 400)

    def test_editing_notes_does_not_recheck_conflicts(self):
        shift_id = self.create().data["id"]
        response = self.client.patch(f"/api/shifts/{shift_id}/", {"notes": "Bring the new menu"})
        self.assertEqual(response.status_code, 200)

    def test_only_managers_delete(self):
        shift_id = self.create().data["id"]
        self.client.force_authenticate(self.worker)
        self.assertEqual(self.client.delete(f"/api/shifts/{shift_id}/").status_code, 403)
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.client.delete(f"/api/shifts/{shift_id}/").status_code, 204)
