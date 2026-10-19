"""Regression guards for Stage 21.6.X2b parity reconciliation."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

from rom_v2.application.integration_evidence import (
    SNAPSHOT_ADAPTER_CONNECTED,
    SNAPSHOT_CONSUMER_WIRING,
    SNAPSHOT_END_TO_END_ACCEPTED,
    SNAPSHOT_INTEGRATION_EVIDENCE_LEVEL,
    SNAPSHOT_RUNTIME_DISPATCH_VERIFIED,
)
from rom_v2.infrastructure.persistence.provisional_contracts import (
    PROVISIONAL_CONTRACT_STATUS,
    PROVISIONAL_GAMEPLAY_TABLES,
    require_authoritative_gameplay_table,
)

EXPECTED_PROVISIONAL_TABLES = frozenset(
    {
                "item_reservations",
        "quest_progress",
        "quest_item_balances",
    }
)
ALLOWED_PROVISIONAL_REFERENCE_FILES = {
    "rom_v2/infrastructure/persistence/provisional_contracts.py",
    "rom_v2/infrastructure/persistence/schema_contract.py",
    "rom_v2/infrastructure/persistence/migrations/v001_v2_baseline.py",
}


class RetrospectiveParityReconciliationTests(unittest.TestCase):
    def test_future_gameplay_tables_are_exactly_provisional(self) -> None:
        self.assertEqual(PROVISIONAL_CONTRACT_STATUS, "PROVISIONAL_RESERVED")
        self.assertEqual(PROVISIONAL_GAMEPLAY_TABLES, EXPECTED_PROVISIONAL_TABLES)

    def test_provisional_tables_fail_closed(self) -> None:
        for table_name in sorted(EXPECTED_PROVISIONAL_TABLES):
            with self.subTest(table_name=table_name):
                with self.assertRaisesRegex(RuntimeError, "provisional_persistence_contract"):
                    require_authoritative_gameplay_table(table_name)
        require_authoritative_gameplay_table("accounts")

    def test_no_production_adapter_uses_provisional_tables(self) -> None:
        project_root = Path(__file__).resolve().parent.parent
        violations = []
        for path in sorted((project_root / "rom_v2").rglob("*.py")):
            relative = path.relative_to(project_root).as_posix()
            if relative in ALLOWED_PROVISIONAL_REFERENCE_FILES:
                continue
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=relative)
            strings = {
                node.value.casefold()
                for node in ast.walk(tree)
                if isinstance(node, ast.Constant) and isinstance(node.value, str)
            }
            for table_name in EXPECTED_PROVISIONAL_TABLES:
                if any(table_name in value for value in strings):
                    violations.append(f"{relative}:{table_name}")
        self.assertEqual(violations, [])

    def test_snapshot_integration_evidence_is_api_ready_only(self) -> None:
        self.assertEqual(SNAPSHOT_INTEGRATION_EVIDENCE_LEVEL, "API_READY")
        self.assertEqual(
            SNAPSHOT_CONSUMER_WIRING,
            {"profile": "DEFERRED", "combat": "DEFERRED", "simulator": "DEFERRED"},
        )
        self.assertFalse(SNAPSHOT_ADAPTER_CONNECTED)
        self.assertFalse(SNAPSHOT_RUNTIME_DISPATCH_VERIFIED)
        self.assertFalse(SNAPSHOT_END_TO_END_ACCEPTED)


if __name__ == "__main__":
    unittest.main()
