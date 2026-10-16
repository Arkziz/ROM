"""Tests for ROM V2 structured logging and redaction."""
from __future__ import annotations

import io
import json
import logging
import unittest

from rom_v2.structured_logging import JsonLogFormatter, LogContext, log_event


class StructuredLoggingTest(unittest.TestCase):
    """Verify required fields, stable keys, and secret-safe output."""

    def _logger(self, stream: io.StringIO) -> logging.Logger:
        """Create an isolated logger writing into the supplied stream."""
        logger = logging.Logger("test.structured")
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JsonLogFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def test_event_contains_diagnostic_fields_and_redacts_secrets(self) -> None:
        """Emit a parseable record without sensitive payload disclosure."""
        stream = io.StringIO(); logger = self._logger(stream)
        protected = "unit-test-protected-value"
        log_event(logger, logging.INFO, "bootstrap.started", LogContext("corr-1", "bootstrap.start"), details={"token": protected, "nested": {"password": protected}, "count": 1})
        record = json.loads(stream.getvalue())
        self.assertEqual(record["correlation_id"], "corr-1")
        self.assertEqual(record["operation"], "bootstrap.start")
        self.assertEqual(record["error_category"], "none")
        self.assertEqual(record["details"]["token"], "<redacted>")
        self.assertNotIn(protected, stream.getvalue())

    def test_invalid_keys_and_error_category_are_rejected(self) -> None:
        """Reject presentation-shaped identifiers and unknown categories."""
        logger = self._logger(io.StringIO())
        with self.assertRaisesRegex(ValueError, "invalid_event_key"):
            log_event(logger, logging.INFO, "human text", LogContext("corr-2", "bootstrap.start"))
        with self.assertRaisesRegex(ValueError, "invalid_operation_key"):
            log_event(logger, logging.INFO, "bootstrap.started", LogContext("corr-2", "human text"))
        with self.assertRaisesRegex(ValueError, "invalid_error_category"):
            log_event(logger, logging.ERROR, "bootstrap.failed", LogContext("corr-2", "bootstrap.start"), error_category="other")

    def test_unknown_object_is_not_stringified(self) -> None:
        """Prevent arbitrary object repr from leaking through details."""
        stream = io.StringIO(); logger = self._logger(stream)
        log_event(logger, logging.INFO, "bootstrap.started", LogContext("corr-3", "bootstrap.start"), details={"object": object()})
        self.assertEqual(json.loads(stream.getvalue())["details"]["object"], "<unsupported>")


if __name__ == "__main__":
    unittest.main()
