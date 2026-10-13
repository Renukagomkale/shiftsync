from django.core.cache import cache
from rest_framework.test import APITestCase

from .models import Business, User


class AccountsTests(APITestCase):
    def setUp(self):
        cache.clear()

    def register(self, role="worker", email="maya@example.com"):
        response = self.client.post(
            "/api/auth/register/",
            {"name": "Maya Joshi", "email": email, "password": "Sunny-day-42", "role": role},
        )
        return response

    def sign_in_as(self, response):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + response.data["access"])

    def create_business(self):
        manager = self.register(role="manager", email="priya@example.com")
        self.sign_in_as(manager)
        response = self.client.post("/api/business/", {"name": "Corner Brew Cafe", "timezone": "Asia/Kolkata"})
        self.client.credentials()
        return response

    def test_register_returns_user_and_tokens(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)
        self.assertIn("access", response.data)
        self.assertIsNone(response.data["user"]["business"])
        self.assertNotIn("password", response.data["user"])

    def test_duplicate_email_is_rejected_regardless_of_case(self):
        self.register()
        response = self.register(email="MAYA@example.com")
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data["errors"])

    def test_weak_password_is_rejected(self):
        response = self.client.post(
            "/api/auth/register/", {"name": "A", "email": "a@example.com", "password": "12345678", "role": "worker"}
        )
        self.assertEqual(response.status_code, 400)

    def test_login_with_email(self):
        self.register()
        response = self.client.post("/api/auth/login/", {"email": "maya@example.com", "password": "Sunny-day-42"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_me_requires_authentication(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_manager_creates_business_and_sees_join_code(self):
        response = self.create_business()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data["join_code"]), 8)
        self.assertEqual(User.objects.get(email="priya@example.com").business.name, "Corner Brew Cafe")

    def test_worker_cannot_create_business(self):
        self.sign_in_as(self.register())
        response = self.client.post("/api/business/", {"name": "Sneaky Shop"})
        self.assertEqual(response.status_code, 403)

    def test_invalid_timezone_is_rejected(self):
        self.sign_in_as(self.register(role="manager"))
        response = self.client.post("/api/business/", {"name": "Cafe", "timezone": "Mars/Base"})
        self.assertEqual(response.status_code, 400)

    def test_worker_joins_with_lowercase_code_and_cannot_see_it(self):
        code = self.create_business().data["join_code"]
        self.sign_in_as(self.register())
        response = self.client.post("/api/business/join/", {"join_code": code.lower()})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("join_code", response.data)
        self.assertEqual(User.objects.get(email="maya@example.com").business.join_code, code)

    def test_wrong_join_code_is_rejected(self):
        self.create_business()
        self.sign_in_as(self.register())
        response = self.client.post("/api/business/join/", {"join_code": "WRONG123"})
        self.assertEqual(response.status_code, 400)

    def test_worker_cannot_join_twice(self):
        code = self.create_business().data["join_code"]
        self.sign_in_as(self.register())
        self.client.post("/api/business/join/", {"join_code": code})
        response = self.client.post("/api/business/join/", {"join_code": code})
        self.assertEqual(response.status_code, 400)

    def test_manager_updates_rules_and_worker_cannot(self):
        code = self.create_business().data["join_code"]
        manager = self.client.post("/api/auth/login/", {"email": "priya@example.com", "password": "Sunny-day-42"})
        self.sign_in_as(manager)
        response = self.client.patch("/api/business/", {"max_hours_per_week": 30, "min_rest_hours": 12})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Business.objects.get(join_code=code).max_hours_per_week, 30)
        self.sign_in_as(self.register())
        self.client.post("/api/business/join/", {"join_code": code})
        self.assertEqual(self.client.patch("/api/business/", {"max_hours_per_week": 99}).status_code, 403)

    def test_members_list_shows_only_my_business_and_hides_emails(self):
        code = self.create_business().data["join_code"]
        self.sign_in_as(self.register())
        self.client.post("/api/business/join/", {"join_code": code})
        other = Business.objects.create(name="Other Shop")
        User.objects.create_user(email="stranger@example.com", password="Sunny-day-42", name="Stranger", business=other)
        response = self.client.get("/api/business/members/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(member["name"] for member in response.data), ["Maya Joshi", "Maya Joshi"])
        self.assertNotIn("email", response.data[0])

    def test_members_requires_a_business(self):
        self.sign_in_as(self.register())
        self.assertEqual(self.client.get("/api/business/members/").status_code, 404)
