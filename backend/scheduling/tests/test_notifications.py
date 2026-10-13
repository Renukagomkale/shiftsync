from rest_framework.test import APITestCase

from scheduling.models import Notification, Shift

from .base import future, make_business, make_user


class NotificationTests(APITestCase):
    def setUp(self):
        self.business = make_business(min_rest_hours=10, max_hours_per_week=60)
        self.manager = make_user(self.business, "priya@example.com", "manager")
        self.maya = make_user(self.business, "maya@example.com")
        self.arjun = make_user(self.business, "arjun@example.com")
        self.sana = make_user(self.business, "sana@example.com")
        self.shift = Shift.objects.create(
            business=self.business, position="Barista", start=future(1, 8), end=future(1, 14), assigned_to=self.maya
        )

    def count(self, user):
        return Notification.objects.filter(user=user).count()

    def request_swap(self, target=None):
        self.client.force_authenticate(self.maya)
        return self.client.post("/api/swaps/", {"shift": self.shift.id, "target_worker": target.id if target else None})

    def act(self, swap_id, action, by):
        self.client.force_authenticate(by)
        return self.client.patch(f"/api/swaps/{swap_id}/", {"action": action})

    def accepted_swap(self):
        swap_id = self.request_swap(self.arjun).data["id"]
        self.act(swap_id, "accept", self.arjun)
        return swap_id

    def test_direct_request_notifies_only_the_target(self):
        self.request_swap(self.arjun)
        self.assertEqual(self.count(self.arjun), 1)
        self.assertEqual(self.count(self.sana), 0)
        message = Notification.objects.get(user=self.arjun).message
        self.assertIn("Maya", message)
        self.assertIn("Barista", message)

    def test_open_request_notifies_coworkers_but_not_requester_or_manager(self):
        self.request_swap()
        self.assertEqual([self.count(u) for u in (self.arjun, self.sana)], [1, 1])
        self.assertEqual([self.count(u) for u in (self.maya, self.manager)], [0, 0])

    def test_accept_notifies_requester_and_manager(self):
        self.accepted_swap()
        self.assertEqual(self.count(self.maya), 1)
        self.assertEqual(self.count(self.manager), 1)

    def test_approval_notifies_both_people(self):
        swap_id = self.accepted_swap()
        self.act(swap_id, "approve", self.manager)
        self.assertEqual(self.count(self.maya), 2)
        self.assertEqual(self.count(self.arjun), 2)

    def test_failed_approval_creates_no_notifications(self):
        swap_id = self.accepted_swap()
        Shift.objects.create(
            business=self.business, position="Floor", start=future(1, 10), end=future(1, 16), assigned_to=self.arjun
        )
        before = Notification.objects.count()
        self.assertEqual(self.act(swap_id, "approve", self.manager).status_code, 400)
        self.assertEqual(Notification.objects.count(), before)

    def test_list_is_private_and_newest_first(self):
        swap_id = self.accepted_swap()
        self.act(swap_id, "approve", self.manager)
        self.client.force_authenticate(self.maya)
        results = self.client.get("/api/notifications/").data["results"]
        self.assertEqual(len(results), 2)
        self.assertIn("approved", results[0]["message"])
        self.client.force_authenticate(self.sana)
        self.assertEqual(self.client.get("/api/notifications/").data["count"], 0)

    def test_mark_one_read_and_unread_filter(self):
        swap_id = self.accepted_swap()
        self.act(swap_id, "approve", self.manager)
        self.client.force_authenticate(self.maya)
        first = self.client.get("/api/notifications/").data["results"][0]["id"]
        self.assertEqual(self.client.patch(f"/api/notifications/{first}/", {"is_read": True}).status_code, 200)
        self.assertEqual(self.client.get("/api/notifications/", {"unread": "true"}).data["count"], 1)
        self.assertEqual(self.client.get("/api/notifications/unread-count/").data["count"], 1)

    def test_mark_all_read(self):
        self.accepted_swap()
        self.client.force_authenticate(self.maya)
        self.assertEqual(self.client.post("/api/notifications/read-all/").data["updated"], 1)
        self.assertEqual(self.client.get("/api/notifications/unread-count/").data["count"], 0)

    def test_cannot_touch_someone_elses_notification(self):
        self.request_swap(self.arjun)
        notification = Notification.objects.get(user=self.arjun)
        self.client.force_authenticate(self.sana)
        response = self.client.patch(f"/api/notifications/{notification.id}/", {"is_read": True})
        self.assertEqual(response.status_code, 404)

    def test_message_text_cannot_be_edited(self):
        self.request_swap(self.arjun)
        notification = Notification.objects.get(user=self.arjun)
        self.client.force_authenticate(self.arjun)
        self.client.patch(f"/api/notifications/{notification.id}/", {"message": "Hacked"})
        notification.refresh_from_db()
        self.assertNotEqual(notification.message, "Hacked")

    def test_cancel_after_acceptance_tells_everyone_involved(self):
        swap_id = self.accepted_swap()
        self.act(swap_id, "cancel", self.maya)
        self.assertEqual(self.count(self.arjun), 2)
        self.assertEqual(self.count(self.manager), 2)
