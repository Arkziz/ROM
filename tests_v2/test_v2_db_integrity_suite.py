"""Tests for the canonical ROM V2 database integrity suite."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.run_v2_db_integrity import run_suite


class V2DatabaseIntegritySuiteTest(unittest.TestCase):
    """Verify complete, repeatable, and failure-free integrity evidence."""

    def test_full_suite_passes_on_clean_workspace(self) -> None:
        """Require every canonical integrity category to pass."""
        with tempfile.TemporaryDirectory() as directory:
            result = run_suite(Path(directory))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["check_count"], 6)
        self.assertEqual(result["failed_checks"], [])

    def test_full_suite_is_repeatable(self) -> None:
        """Run twice in fresh workspaces without accumulated local-state dependence."""
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = run_suite(Path(first))
            two = run_suite(Path(second))
        self.assertEqual(one["status"], "PASS")
        self.assertEqual(two["status"], "PASS")
        self.assertEqual(
            [item["check_id"] for item in one["checks"]],
            [item["check_id"] for item in two["checks"]],
        )


if __name__ == "__main__":
    unittest.main()
