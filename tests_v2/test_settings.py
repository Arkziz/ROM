"""Tests for validated and redacted ROM V2 settings."""
from __future__ import annotations

import unittest
from pathlib import Path

from rom_v2.settings import ConfigurationError, SecretValue, V2Settings


class V2SettingsTest(unittest.TestCase):
    """Verify validation, redaction, and safe diagnostics."""

    def test_valid_environment_is_loaded_without_secret_disclosure(self) -> None:
        """Load settings and prove every presentation path stays redacted."""
        protected_value = "unit-test-only-value"
        settings = V2Settings.from_environment(
            Path("."),
            {
                "ROM_V2_BOT_TOKEN": protected_value,
                "ROM_V2_ENVIRONMENT": "test",
                "ROM_V2_LOG_LEVEL": "debug",
            },
        )
        self.assertEqual(settings.bot_token.reveal(), protected_value)
        self.assertNotIn(protected_value, repr(settings.bot_token))
        self.assertNotIn(protected_value, str(settings.bot_token))
        self.assertNotIn(protected_value, repr(settings))
        self.assertNotIn(protected_value, repr(settings.safe_summary()))

    def test_missing_secret_is_rejected_with_stable_reason(self) -> None:
        """Reject an absent token without echoing any environment content."""
        with self.assertRaisesRegex(ConfigurationError, "missing_required_secret"):
            V2Settings.from_environment(Path("."), {})

    def test_invalid_values_are_rejected(self) -> None:
        """Reject unsupported environment and log-level values."""
        with self.assertRaisesRegex(ConfigurationError, "invalid_environment"):
            V2Settings.from_environment(
                Path("."),
                {"ROM_V2_BOT_TOKEN": "unit-test-only-value", "ROM_V2_ENVIRONMENT": "invalid"},
            )
        with self.assertRaisesRegex(ConfigurationError, "invalid_log_level"):
            V2Settings.from_environment(
                Path("."),
                {"ROM_V2_BOT_TOKEN": "unit-test-only-value", "ROM_V2_LOG_LEVEL": "TRACE"},
            )


class SecretValueTest(unittest.TestCase):
    """Verify the dedicated secret wrapper independently."""

    def test_empty_secret_is_rejected(self) -> None:
        """Reject whitespace-only secret values."""
        with self.assertRaises(ConfigurationError):
            SecretValue.from_required("   ", "ROM_V2_BOT_TOKEN")


if __name__ == "__main__":
    unittest.main()
