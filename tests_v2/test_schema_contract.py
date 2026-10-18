"""Tests for complete ROM V2 schema column and constraint contracts."""
from __future__ import annotations
import unittest
from rom_v2.infrastructure.persistence.schema_contract import SCHEMA_CONTRACT
from tools.verify_v2_schema_contract import verify_contract

class StrengthenedSchemaContractTest(unittest.TestCase):
    """Verify DDL-ready metadata without creating the physical database."""
    def test_complete_contract_passes(self) -> None:
        """Require all owners, types, nullability, constraints, and FK actions."""
        result=verify_contract(); self.assertEqual(result["status"], "PASS"); self.assertEqual(result["contract_revision"], "21.5.1b")
    def test_money_and_mutable_counts_use_integer_storage(self) -> None:
        """Prevent float money and unconstrained inventory quantities."""
        tables=dict(SCHEMA_CONTRACT["tables"])
        self.assertEqual(tables["gold_wallets"]["columns"]["balance_minor"]["storage_type"], "INTEGER")
        self.assertIn("balance_minor >= 0", tables["gold_wallets"]["columns"]["balance_minor"]["checks"])
        self.assertIn("quantity > 0", tables["item_instances"]["columns"]["quantity"]["checks"])
    def test_nullable_fields_are_explicit(self) -> None:
        """Keep optional timestamps and resource values explicit in the contract."""
        tables=dict(SCHEMA_CONTRACT["tables"])
        self.assertTrue(tables["characters"]["columns"]["current_mp"]["nullable"])
        self.assertTrue(tables["outbox_messages"]["columns"]["published_at_utc"]["nullable"])
        self.assertFalse(tables["accounts"]["columns"]["registered_at_utc"]["nullable"])
    def test_foreign_key_actions_are_explicit(self) -> None:
        """Require lifecycle behavior on every relationship."""
        tables=dict(SCHEMA_CONTRACT["tables"])
        for table in tables.values():
            for fk in table.get("foreign_keys", []):
                self.assertIn(fk["on_delete"], {"CASCADE", "RESTRICT", "SET NULL", "NO ACTION"})
                self.assertIn(fk["on_update"], {"CASCADE", "RESTRICT", "SET NULL", "NO ACTION"})
    def test_unimplemented_domains_are_explicitly_deferred(self) -> None:
        """Avoid premature placeholder tables while preserving ownership decisions."""
        deferred=dict(SCHEMA_CONTRACT["deferred_domains"])
        self.assertIn("guild", deferred); self.assertIn("auction", deferred); self.assertIn("runes_sockets", deferred)
        self.assertTrue(all(item["decision"] == "deferred_no_placeholder_table" for item in deferred.values()))

    def test_completion_timestamps_are_bidirectional(self) -> None:
        """Reject timestamps on non-completed quest and operation states."""
        tables = dict(SCHEMA_CONTRACT["tables"])
        quest_check = "(state_key = 'completed' AND completed_at_utc IS NOT NULL) OR (state_key <> 'completed' AND completed_at_utc IS NULL)"
        operation_check = "(status_key = 'completed' AND completed_at_utc IS NOT NULL) OR (status_key <> 'completed' AND completed_at_utc IS NULL)"
        self.assertIn(quest_check, tables["quest_progress"]["checks"])
        self.assertIn(operation_check, tables["operation_records"]["checks"])

    def test_exact_once_dependents_reference_operation_records(self) -> None:
        """Require ledger evidence and reservation ownership to reference operations."""
        tables = dict(SCHEMA_CONTRACT["tables"])
        ledger_fks = tables["crystal_ledger"]["foreign_keys"]
        reservation_fks = tables["item_reservations"]["foreign_keys"]
        self.assertIn({"column": "operation_id", "target_table": "operation_records", "target_column": "operation_id", "on_delete": "RESTRICT", "on_update": "CASCADE"}, ledger_fks)
        self.assertIn({"column": "operation_id", "target_table": "operation_records", "target_column": "operation_id", "on_delete": "CASCADE", "on_update": "CASCADE"}, reservation_fks)

if __name__ == "__main__": unittest.main()
