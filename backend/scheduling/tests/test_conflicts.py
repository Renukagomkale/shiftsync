from django.test import TestCase

from scheduling.models import Shift
from scheduling.services.conflicts import find_conflicts

from .base import at, make_business, make_user

KOLKATA = "Asia/Kolkata"


def codes(conflicts):
    return {conflict["code"] for conflict in conflicts}


class ConflictTests(TestCase):
    def setUp(self):
        self.business = make_business(min_rest_hours=0, max_hours_per_week=40)
        self.worker = make_user(self.business, "maya@example.com")

    def book(self, start, end):
        return Shift.objects.create(
            business=self.business, position="Barista", start=start, end=end, assigned_to=self.worker
        )

    def check(self, start, end, exclude=None):
        return find_conflicts(self.business, self.worker, start, end, exclude)

    def test_partial_overlap_is_a_conflict(self):
        self.book(at(0, 9), at(0, 13))
        self.assertEqual(codes(self.check(at(0, 12), at(0, 16))), {"overlap"})

    def test_shift_inside_another_shift_is_a_conflict(self):
        self.book(at(0, 9), at(0, 17))
        self.assertEqual(codes(self.check(at(0, 11), at(0, 13))), {"overlap"})

    def test_back_to_back_shifts_do_not_overlap(self):
        self.book(at(0, 9), at(0, 13))
        self.assertEqual(self.check(at(0, 13), at(0, 17)), [])

    def test_editing_a_shift_ignores_itself(self):
        shift = self.book(at(0, 9), at(0, 13))
        self.assertEqual(self.check(at(0, 10), at(0, 14), exclude=shift), [])

    def test_back_to_back_breaks_the_rest_rule(self):
        self.business.min_rest_hours = 10
        self.book(at(0, 9), at(0, 13))
        self.assertEqual(codes(self.check(at(0, 13), at(0, 17))), {"rest_gap"})

    def test_rest_gap_after_a_shift(self):
        self.business.min_rest_hours = 10
        self.book(at(0, 14), at(0, 22))
        self.assertEqual(codes(self.check(at(1, 6), at(1, 12))), {"rest_gap"})
        self.assertEqual(self.check(at(1, 8), at(1, 12)), [])

    def test_rest_gap_before_a_shift(self):
        self.business.min_rest_hours = 10
        self.book(at(1, 6), at(1, 12))
        self.assertEqual(codes(self.check(at(0, 14), at(0, 22))), {"rest_gap"})

    def test_weekly_hours_limit(self):
        self.business.max_hours_per_week = 30
        for day in range(3):
            self.book(at(day, 9), at(day, 17))
        self.assertEqual(codes(self.check(at(3, 9), at(3, 17))), {"weekly_hours"})
        self.assertEqual(self.check(at(3, 9), at(3, 15)), [])

    def test_hours_from_other_weeks_do_not_count(self):
        self.business.max_hours_per_week = 10
        self.book(at(-1, 9), at(-1, 17))
        self.assertEqual(self.check(at(0, 9), at(0, 17)), [])

    def test_week_boundary_follows_business_timezone(self):
        business = make_business(timezone=KOLKATA, min_rest_hours=0, max_hours_per_week=10)
        worker = make_user(business, "kolkata@example.com")
        Shift.objects.create(
            business=business,
            position="Floor",
            start=at(-1, 15, tz=KOLKATA),
            end=at(-1, 23, tz=KOLKATA),
            assigned_to=worker,
        )
        result = find_conflicts(business, worker, at(0, 0, 30, tz=KOLKATA), at(0, 6, 30, tz=KOLKATA))
        self.assertEqual(result, [])

    def test_several_problems_are_reported_together(self):
        self.business.min_rest_hours = 10
        self.business.max_hours_per_week = 10
        self.book(at(0, 9), at(0, 17))
        self.assertEqual(codes(self.check(at(0, 12), at(0, 20))), {"overlap", "weekly_hours"})
