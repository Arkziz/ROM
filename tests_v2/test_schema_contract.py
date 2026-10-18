"""Tests for the ROM V2 domain-oriented schema contract."""
from __future__ import annotations
import unittest
from rom_v2.infrastructure.persistence.schema_contract import SCHEMA_CONTRACT
from tools.verify_v2_schema_contract import verify_contract

class SchemaContractTest(unittest.TestCase):
    """Verify ownership, normalization boundaries, and persistence invariants."""
    def test_contract_passes_verifier(self) -> None:
        """Require the canonical ER inventory to satisfy all mandatory rules."""
        self.assertEqual(verify_contract()["status"], "PASS")
    def test_account_and_character_ownership_are_separate(self) -> None:
        """Keep account lifetime independent from the single current character."""
        tables=dict(SCHEMA_CONTRACT["tables"])
        self.assertEqual(tables["accounts"]["owner"], "account")
        self.assertEqual(tables["characters"]["owner"], "character")
        self.assertIn(["account_id"], tables["characters"]["unique"])
    def test_exact_once_and_outbox_tables_exist(self) -> None:
        """Preserve operation, event, and publication atomicity contracts."""
        tables=dict(SCHEMA_CONTRACT["tables"])
        self.assertTrue(tables["domain_events"]["append_only"])
        self.assertIn("operation_records", tables)
        self.assertIn("outbox_messages", tables)
    def test_money_and_time_are_storage_safe(self) -> None:
        """Reject float money and local-time persistence at the schema boundary."""
        self.assertEqual(SCHEMA_CONTRACT["money_policy"], "integer_minor_units")
        self.assertEqual(SCHEMA_CONTRACT["timestamp_policy"], "utc_iso8601_text")
if __name__ == "__main__": unittest.main()
