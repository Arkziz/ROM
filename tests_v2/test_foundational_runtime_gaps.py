from __future__ import annotations

import unittest
from datetime import datetime, timezone

from rom_v2.app.foundation_runtime import (
    REQUIRED_FOUNDATION_PORTS,
    reject_forbidden_runtime_import,
    validate_foundation_runtime_ports,
)
from rom_v2.domain.utc_time import normalize_utc, utc_now


class FoundationalRuntimeGapsTest(unittest.TestCase):
    def test_utc_owner_normalizes_and_rejects_naive_values(self) -> None:
        value = datetime(2026, 1, 1, 2, tzinfo=timezone.utc)
        self.assertEqual(normalize_utc(value, "value"), value)
        self.assertIsNotNone(utc_now().utcoffset())
        with self.assertRaisesRegex(ValueError, "value_must_be_timezone_aware"):
            normalize_utc(datetime(2026, 1, 1), "value")

    def test_foundation_fails_closed_for_missing_or_null_ports(self) -> None:
        self.assertFalse(validate_foundation_runtime_ports({}).ready)
        ports = {name: object() for name in REQUIRED_FOUNDATION_PORTS}
        ports["clock"] = None
        self.assertEqual(validate_foundation_runtime_ports(ports).reason, "null_required_ports")

    def test_foundation_accepts_complete_port_set(self) -> None:
        ports = {name: object() for name in REQUIRED_FOUNDATION_PORTS}
        self.assertTrue(validate_foundation_runtime_ports(ports).ready)

    def test_v1_and_legacy_import_roots_are_rejected(self) -> None:
        for module_name in ("handlers.start", "systems.combat", "db_modules.users", "legacy.v1"):
            with self.assertRaisesRegex(ValueError, "forbidden_runtime_import"):
                reject_forbidden_runtime_import(module_name)


if __name__ == "__main__":
    unittest.main()
