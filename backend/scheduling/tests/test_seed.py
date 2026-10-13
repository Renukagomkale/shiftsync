from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from accounts.models import Business, User
from scheduling.models import Shift, SwapRequest
from scheduling.services.conflicts import find_conflicts


class SeedDemoTests(TestCase):
    def seed(self, *args):
        output = StringIO()
        call_command("seed_demo", *args, stdout=output)
        return output.getvalue()

    def test_creates_a_team_shifts_and_swaps(self):
        self.seed()
        business = Business.objects.get(name="Corner Brew Cafe")
        self.assertEqual(User.objects.filter(business=business).count(), 5)
        self.assertEqual(Shift.objects.filter(business=business).count(), 34)
        statuses = sorted(SwapRequest.objects.values_list("status", flat=True))
        self.assertEqual(statuses, ["pending_manager", "pending_peer", "pending_peer"])

    def test_demo_shifts_respect_the_scheduling_rules(self):
        self.seed()
        business = Business.objects.get(name="Corner Brew Cafe")
        for shift in Shift.objects.filter(business=business, assigned_to__isnull=False):
            conflicts = find_conflicts(business, shift.assigned_to, shift.start, shift.end, exclude_shift=shift)
            self.assertEqual(conflicts, [], f"{shift} breaks a rule")

    def test_running_twice_does_not_duplicate_and_reset_rebuilds(self):
        self.seed()
        self.assertIn("already exists", self.seed())
        self.assertEqual(Shift.objects.count(), 34)
        self.seed("--reset")
        self.assertEqual(Shift.objects.count(), 34)
        self.assertEqual(Business.objects.count(), 1)
