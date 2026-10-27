from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from rom_v2.domain.events import (
    DirectRewardCatalog,
    EventDefinition,
    EventLifecycle,
    EventSchedule,
    EventScheduleRewardService,
)


class EventScheduleRewardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.start = datetime(2026, 1, 10, 8, 0, tzinfo=timezone.utc)
        self.end = self.start + timedelta(days=2)
        self.definition = EventDefinition(
            "test_event_2026", EventSchedule(self.start, self.end), enabled=True
        )
        self.service = EventScheduleRewardService(
            (self.definition,), (DirectRewardCatalog("test_event_2026", ()),)
        )

    def test_start_is_inclusive_and_end_is_exclusive(self) -> None:
        self.assertEqual(self.service.evaluate("test_event_2026", self.start).lifecycle, EventLifecycle.ACTIVE)
        self.assertEqual(self.service.evaluate("test_event_2026", self.end).lifecycle, EventLifecycle.COMPLETED)

    def test_upcoming_active_completed_are_clock_deterministic(self) -> None:
        self.assertEqual(self.service.evaluate("test_event_2026", self.start - timedelta(microseconds=1)).lifecycle, EventLifecycle.UPCOMING)
        self.assertEqual(self.service.evaluate("test_event_2026", self.start + timedelta(hours=1)).lifecycle, EventLifecycle.ACTIVE)
        self.assertEqual(self.service.evaluate("test_event_2026", self.end + timedelta(seconds=1)).lifecycle, EventLifecycle.COMPLETED)

    def test_disabled_event_is_not_eligible(self) -> None:
        disabled = EventDefinition("disabled", EventSchedule(self.start, self.end), enabled=False)
        result = EventScheduleRewardService((disabled,)).evaluate("disabled", self.start)
        self.assertEqual(result.lifecycle, EventLifecycle.DISABLED)
        self.assertFalse(result.eligible)

    def test_timezone_aware_values_are_normalized_to_utc(self) -> None:
        plus_two = timezone(timedelta(hours=2))
        schedule = EventSchedule(self.start.astimezone(plus_two), self.end.astimezone(plus_two))
        self.assertEqual(schedule.start_at, self.start)
        self.assertEqual(schedule.end_at, self.end)

    def test_naive_time_and_invalid_window_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone_aware"):
            EventSchedule(datetime(2026, 1, 1), self.end)
        with self.assertRaisesRegex(ValueError, "must_precede"):
            EventSchedule(self.end, self.start)

    def test_unknown_and_duplicate_event_keys_fail_closed(self) -> None:
        with self.assertRaisesRegex(KeyError, "unknown_event_key"):
            self.service.evaluate("missing", self.start)
        with self.assertRaisesRegex(ValueError, "duplicate_event_key"):
            EventScheduleRewardService((self.definition, self.definition))

    def test_v1_parity_has_no_direct_test_event_reward(self) -> None:
        result = self.service.evaluate("test_event_2026", self.start)
        self.assertTrue(result.eligible)
        self.assertEqual(result.direct_reward_item_ids, ())

    def test_reward_catalog_does_not_model_shop_or_drop_quantities(self) -> None:
        catalog = DirectRewardCatalog("event", (4000, 4001))
        self.assertEqual(catalog.item_ids, (4000, 4001))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            DirectRewardCatalog("event", (4000, 4000))


if __name__ == "__main__":
    unittest.main()
