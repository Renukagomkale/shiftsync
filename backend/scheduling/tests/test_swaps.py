from rest_framework.test import APITestCase

from scheduling.models import Shift, SwapRequest

from .base import future, make_business, make_user


class SwapTests(APITestCase):
    def setUp(self):
        self.business = make_business(min_rest_hours=10, max_hours_per_week=60)
        self.manager = make_user(self.business, "priya@example.com", "manager")
        self.maya = make_user(self.business, "maya@example.com")
        self.arjun = make_user(self.business, "arjun@example.com")
        self.sana = make_user(self.business, "sana@example.com")
        self.shift = self.book(self.maya, 1, 8, 14)

    def book(self, worker, day, start_hour, end_hour):
        return Shift.objects.create(
            business=self.business,
            position="Barista",
            start=future(day, start_hour),
            end=future(day, end_hour),
            assigned_to=worker,
        )

    def request_swap(self, shift=None, target=None, by=None):
        self.client.force_authenticate(by or self.maya)
        return self.client.post(
            "/api/swaps/", {"shift": (shift or self.shift).id, "target_worker": target.id if target else None}
        )

    def act(self, swap_id, action, by):
        self.client.force_authenticate(by)
        return self.client.patch(f"/api/swaps/{swap_id}/", {"action": action})

    def waiting_for_manager(self, shift=None, target=None, by=None):
        target = target or self.arjun
        swap_id = self.request_swap(shift=shift, target=target, by=by).data["id"]
        self.act(swap_id, "accept", target)
        return swap_id

    def test_worker_requests_swap_for_own_shift(self):
        response = self.request_swap(target=self.arjun)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "pending_peer")
        self.assertEqual(response.data["requested_by"], self.maya.id)
        self.assertEqual(response.data["target_worker_name"], self.arjun.name)

    def test_cannot_request_swap_for_someone_elses_shift(self):
        self.assertEqual(self.request_swap(by=self.arjun).status_code, 403)

    def test_cannot_request_swap_for_a_shift_that_started(self):
        started = self.book(self.maya, -1, 9, 12)
        self.assertEqual(self.request_swap(shift=started).status_code, 400)

    def test_cannot_swap_with_yourself(self):
        self.assertEqual(self.request_swap(target=self.maya).status_code, 400)

    def test_only_one_open_swap_per_shift(self):
        self.request_swap(target=self.arjun)
        self.assertEqual(self.request_swap(target=self.sana).status_code, 400)

    def test_target_accepts_and_swap_waits_for_manager(self):
        swap_id = self.request_swap(target=self.arjun).data["id"]
        response = self.act(swap_id, "accept", self.arjun)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "pending_manager")

    def test_unrelated_worker_cannot_see_or_accept_a_direct_swap(self):
        swap_id = self.request_swap(target=self.arjun).data["id"]
        self.assertEqual(self.act(swap_id, "accept", self.sana).status_code, 404)

    def test_anyone_can_take_an_open_swap_but_not_the_requester(self):
        swap_id = self.request_swap().data["id"]
        self.assertEqual(self.act(swap_id, "accept", self.maya).status_code, 403)
        response = self.act(swap_id, "accept", self.sana)
        self.assertEqual(response.data["target_worker"], self.sana.id)

    def test_accept_is_blocked_when_it_clashes_with_the_acceptors_shift(self):
        self.book(self.arjun, 1, 10, 16)
        swap_id = self.request_swap(target=self.arjun).data["id"]
        self.assertEqual(self.act(swap_id, "accept", self.arjun).status_code, 400)
        self.assertEqual(SwapRequest.objects.get(pk=swap_id).status, "pending_peer")

    def test_target_declines(self):
        swap_id = self.request_swap(target=self.arjun).data["id"]
        response = self.act(swap_id, "decline", self.arjun)
        self.assertEqual(response.data["status"], "rejected")
        self.assertIsNotNone(response.data["resolved_at"])

    def test_only_the_target_can_decline(self):
        swap_id = self.request_swap().data["id"]
        self.assertEqual(self.act(swap_id, "decline", self.sana).status_code, 403)

    def test_manager_approval_moves_the_shift(self):
        swap_id = self.waiting_for_manager()
        response = self.act(swap_id, "approve", self.manager)
        self.assertEqual(response.data["status"], "approved")
        self.shift.refresh_from_db()
        self.assertEqual(self.shift.assigned_to, self.arjun)

    def test_cannot_approve_before_a_coworker_accepts(self):
        swap_id = self.request_swap(target=self.arjun).data["id"]
        self.assertEqual(self.act(swap_id, "approve", self.manager).status_code, 400)

    def test_workers_cannot_approve_or_reject(self):
        swap_id = self.waiting_for_manager()
        self.assertEqual(self.act(swap_id, "approve", self.arjun).status_code, 403)
        self.assertEqual(self.act(swap_id, "reject", self.maya).status_code, 403)

    def test_approving_twice_is_rejected(self):
        swap_id = self.waiting_for_manager()
        self.act(swap_id, "approve", self.manager)
        self.assertEqual(self.act(swap_id, "approve", self.manager).status_code, 400)

    def test_approval_rechecks_conflicts(self):
        swap_id = self.waiting_for_manager()
        self.book(self.arjun, 1, 10, 16)
        response = self.act(swap_id, "approve", self.manager)
        self.assertEqual(response.status_code, 400)
        self.shift.refresh_from_db()
        self.assertEqual(self.shift.assigned_to, self.maya)
        self.assertEqual(SwapRequest.objects.get(pk=swap_id).status, "pending_manager")

    def test_two_swaps_cannot_double_book_the_same_worker(self):
        second = self.book(self.sana, 1, 10, 16)
        first_swap = self.waiting_for_manager()
        second_swap = self.waiting_for_manager(shift=second, by=self.sana)
        self.assertEqual(self.act(first_swap, "approve", self.manager).status_code, 200)
        self.assertEqual(self.act(second_swap, "approve", self.manager).status_code, 400)
        second.refresh_from_db()
        self.assertEqual(second.assigned_to, self.sana)

    def test_approval_fails_if_the_shift_was_reassigned_meanwhile(self):
        swap_id = self.waiting_for_manager()
        Shift.objects.filter(pk=self.shift.pk).update(assigned_to=self.sana)
        self.assertEqual(self.act(swap_id, "approve", self.manager).status_code, 400)

    def test_manager_rejects_and_shift_stays(self):
        swap_id = self.waiting_for_manager()
        response = self.act(swap_id, "reject", self.manager)
        self.assertEqual(response.data["status"], "rejected")
        self.shift.refresh_from_db()
        self.assertEqual(self.shift.assigned_to, self.maya)

    def test_requester_cancels_but_others_cannot(self):
        swap_id = self.request_swap(target=self.arjun).data["id"]
        self.assertEqual(self.act(swap_id, "cancel", self.arjun).status_code, 403)
        self.assertEqual(self.act(swap_id, "cancel", self.maya).data["status"], "cancelled")

    def test_finished_swaps_cannot_be_changed(self):
        swap_id = self.waiting_for_manager()
        self.act(swap_id, "approve", self.manager)
        self.assertEqual(self.act(swap_id, "cancel", self.maya).status_code, 400)

    def test_a_new_swap_is_allowed_after_the_old_one_closed(self):
        swap_id = self.request_swap(target=self.arjun).data["id"]
        self.act(swap_id, "cancel", self.maya)
        self.assertEqual(self.request_swap(target=self.sana).status_code, 201)

    def test_visibility_by_role_and_business(self):
        self.request_swap(target=self.arjun)
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.client.get("/api/swaps/").data["count"], 1)
        self.client.force_authenticate(self.sana)
        self.assertEqual(self.client.get("/api/swaps/").data["count"], 0)
        outsider = make_user(make_business(name="Other Shop"), "boss@example.com", "manager")
        self.client.force_authenticate(outsider)
        self.assertEqual(self.client.get("/api/swaps/").data["count"], 0)

    def test_list_filters_by_status(self):
        self.request_swap(target=self.arjun)
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.client.get("/api/swaps/", {"status": "pending_peer"}).data["count"], 1)
        self.assertEqual(self.client.get("/api/swaps/", {"status": "approved"}).data["count"], 0)
        self.assertEqual(self.client.get("/api/swaps/", {"status": "nonsense"}).status_code, 400)

    def test_open_swaps_are_visible_to_coworkers(self):
        self.request_swap()
        self.client.force_authenticate(self.sana)
        self.assertEqual(self.client.get("/api/swaps/").data["count"], 1)
