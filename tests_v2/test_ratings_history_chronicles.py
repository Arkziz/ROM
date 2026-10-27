from __future__ import annotations
import unittest
from datetime import datetime, timedelta, timezone
from rom_v2.domain.ratings_history_chronicles import *

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def test_ratings_top_100_page_20_and_stable_ties(self):
        candidates = tuple(RatingCandidate(i, f"p{i}", 1000 - i // 2) for i in range(1, 122))
        view = build_rating_view(candidates, 1, 121)
        self.assertEqual(len(view.page.items), 20)
        self.assertEqual(view.page.total_items, 100)
        self.assertEqual(view.page.total_pages, 5)
        self.assertEqual(view.own_entry.position, 121)
        self.assertLess(view.page.items[0].subject_id, view.page.items[1].subject_id)

    def test_rating_boundary_page_and_duplicate_fail_closed(self):
        entries = tuple(RatingCandidate(i, str(i), i) for i in range(1, 22))
        self.assertEqual(len(build_rating_view(entries, 2).page.items), 1)
        self.assertEqual(build_rating_view(entries, 3).page.items, ())
        with self.assertRaisesRegex(ValueError, "duplicate_rating_subject"):
            build_rating_view((entries[0], entries[0]), 1)

    def test_history_only_completed_trade_and_result_pvp(self):
        trade = HistoryRecord("t", 1, self.now, "trade_completed", {})
        pvp = HistoryRecord("p", 1, self.now, "pvp_result", {})
        self.assertEqual(history_page((trade, pvp), 1, "trade_completed", 1).items, (trade,))
        with self.assertRaisesRegex(ValueError, "unsupported_history_kind"):
            history_page((trade,), 1, "trade_pending", 1)

    def test_history_newest_first_and_limit(self):
        records = tuple(HistoryRecord(f"r{i:03}", 1, self.now + timedelta(seconds=i), "trade_completed", {}) for i in range(105))
        page = history_page(records, 1, "trade_completed", 1)
        self.assertEqual(page.total_items, 100)
        self.assertEqual(page.items[0].record_id, "r104")
        self.assertEqual(page.page_size, 10)

    def test_chronicles_last_100_ten_per_page_newest_first(self):
        events = tuple(ChronicleEvent(f"e{i:03}", 7, self.now + timedelta(seconds=i), "event", {}) for i in range(111))
        first = chronicle_page(events, 7, 1)
        last = chronicle_page(events, 7, 10)
        self.assertEqual(first.total_items, 100)
        self.assertEqual(len(first.items), 10)
        self.assertEqual(first.items[0].event_id, "e110")
        self.assertEqual(len(last.items), 10)
        self.assertFalse(last.has_next)

    def test_chronicle_tie_order_is_deterministic(self):
        events = (ChronicleEvent("b", 1, self.now, "x", {}), ChronicleEvent("a", 1, self.now, "x", {}))
        self.assertEqual([x.event_id for x in chronicle_page(events, 1, 1).items], ["a", "b"])

    def test_naive_timestamps_and_duplicate_ids_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "timezone_aware"):
            ChronicleEvent("x", 1, datetime(2026, 1, 1), "x", {})
        event = ChronicleEvent("x", 1, self.now, "x", {})
        with self.assertRaisesRegex(ValueError, "duplicate_chronicle_event_id"):
            retain_chronicles((event, event), 1)

    def test_pages_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "page_must_be_positive"):
            chronicle_page((), 1, 0)
        with self.assertRaisesRegex(ValueError, "page_must_be_positive"):
            build_rating_view((), 0)

if __name__ == "__main__": unittest.main()
