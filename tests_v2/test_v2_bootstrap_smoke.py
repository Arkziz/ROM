"""Smoke tests for the isolated ROM V2 bootstrap."""
from __future__ import annotations

import unittest

from rom_v2.bootstrap import build_lifecycle


class V2BootstrapSmokeTest(unittest.TestCase):
    """Verify lifecycle startup without gameplay or external integrations."""

    def test_start_and_stop_are_isolated(self) -> None:
        """Start and stop while gameplay remains disabled."""
        lifecycle = build_lifecycle()
        lifecycle.start()
        self.assertTrue(lifecycle.started)
        self.assertFalse(lifecycle.container.config.gameplay_enabled)
        lifecycle.stop()
        self.assertFalse(lifecycle.started)


if __name__ == "__main__":
    unittest.main()
