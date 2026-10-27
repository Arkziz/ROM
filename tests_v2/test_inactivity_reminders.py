from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from rom_v2.domain.inactivity_reminders import (
    DEFAULT_INACTIVITY_THRESHOLD,
    InactivityReminderService,
    build_cycle_key,
)


class InactivityReminderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = InactivityReminderService()
        self.activity = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        self.due_at = self.activity + timedelta(days=7)

    def evaluate(self, current, delivered=frozenset(), activity=None):
        return self.service.evaluate(
            user_id=42,
            last_activity_at=activity or self.activity,
            evaluated_at=current,
            delivered_cycle_keys=delivered,
        )

    def test_threshold_is_exactly_seven_full_days(self) -> None:
        self.assertEqual(DEFAULT_INACTIVITY_THRESHOLD, timedelta(days=7))
        self.assertFalse(self.evaluate(self.due_at - timedelta(microseconds=1)).due)
        self.assertTrue(self.evaluate(self.due_at).due)

    def test_evaluation_is_clock_deterministic(self) -> None:
        first = self.evaluate(self.due_at)
        second = self.evaluate(self.due_at)
        self.assertEqual(first, second)

    def test_same_cycle_is_suppressed_by_persistent_audit_key(self) -> None:
        first = self.evaluate(self.due_at)
        replay = self.evaluate(self.due_at + timedelta(days=10), frozenset({first.cycle_key}))
        self.assertFalse(replay.due)
        self.assertTrue(replay.already_delivered)

    def test_new_activity_creates_new_cycle(self) -> None:
        first = self.evaluate(self.due_at)
        new_activity = self.activity + timedelta(days=1)
        second = self.evaluate(new_activity + timedelta(days=7), activity=new_activity)
        self.assertNotEqual(first.cycle_key, second.cycle_key)
        self.assertTrue(second.due)

    def test_cycle_key_is_stable_across_timezone_representation(self) -> None:
        plus_two = timezone(timedelta(hours=2))
        self.assertEqual(
            build_cycle_key(42, self.activity),
            build_cycle_key(42, self.activity.astimezone(plus_two)),
        )

    def test_naive_timestamps_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone_aware"):
            self.service.evaluate(
                user_id=42,
                last_activity_at=datetime(2026, 1, 1),
                evaluated_at=self.due_at,
            )

    def test_noncanonical_threshold_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported"):
            InactivityReminderService(timedelta(days=6))

    def test_receipt_requires_due_cycle_and_success_time(self) -> None:
        not_due = self.evaluate(self.due_at - timedelta(seconds=1))
        with self.assertRaisesRegex(ValueError, "not_deliverable"):
            self.service.receipt_after_successful_delivery(not_due, delivered_at=self.due_at)
        due = self.evaluate(self.due_at)
        receipt = self.service.receipt_after_successful_delivery(due, delivered_at=self.due_at)
        self.assertEqual(receipt.cycle_key, due.cycle_key)

    def test_service_contains_no_scheduler_message_or_transport(self) -> None:
        self.assertFalse(hasattr(self.service, "run_forever"))
        self.assertFalse(hasattr(self.service, "send_message"))
        self.assertFalse(hasattr(self.service, "retry"))


if __name__ == "__main__":
    unittest.main()
