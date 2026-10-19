"""Tests for migration 001 and isolated ROM V2 database recreation."""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from rom_v2.infrastructure.persistence import V2Migrator
from rom_v2.infrastructure.persistence.migrations import MIGRATIONS


EXPECTED_TABLES = {
    "inventory_items",
    "item_definitions",
    "accounts", "characters", "character_primary_stats", "gold_wallets",
    "crystal_wallets", "crystal_ledger", "item_instances", "equipment_slots",
    "item_reservations", "quest_progress", "quest_item_balances",
    "operation_records", "domain_events", "outbox_messages", "schema_migrations",
}


class V2BaselineMigrationTest(unittest.TestCase):
    """Verify clean creation, recreation, constraints, and exact-once migration history."""

    def test_clean_create_and_recreate_are_deterministic(self) -> None:
        """Create the same 15-table schema from an empty runtime directory twice."""
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "rom_v2.db"
            migrator = V2Migrator(database)
            first = migrator.recreate()
            second = migrator.recreate()
            self.assertEqual(set(first.table_names), EXPECTED_TABLES)
            self.assertEqual(first.table_names, second.table_names)
            self.assertEqual(first.applied_versions, (1, 2, 3))
            self.assertEqual(second.applied_versions, (1, 2, 3))
            self.assertEqual(first.foreign_key_violations, ())
            self.assertEqual(second.quick_check, "ok")

    def test_migration_checksum_is_stable(self) -> None:
        """Require one ordered baseline migration with a SHA-256 checksum."""
        self.assertEqual(len(MIGRATIONS), 3)
        self.assertEqual(MIGRATIONS[0].version, 1)
        self.assertEqual(MIGRATIONS[0].key, "001_v2_baseline")
        self.assertEqual(len(MIGRATIONS[0].checksum), 64)

    def test_bidirectional_completion_constraints_are_enforced(self) -> None:
        """Reject completion timestamps that disagree with quest and operation state."""
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "rom_v2.db"
            V2Migrator(database).recreate()
            connection = sqlite3.connect(database)
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("INSERT INTO accounts VALUES ('a', 1, 'active', '2026-01-01T00:00:00Z', 60, 0)")
            connection.execute("INSERT INTO characters VALUES ('c','a','name','class',1,0,'start',10,NULL,0)")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO quest_progress VALUES ('c','q','active','{}','2026-01-01T00:00:00Z',0)")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO operation_records VALUES ('o','k','character','c','in_progress',NULL,'2026-01-01T00:00:00Z','2026-01-01T00:00:00Z')")
            connection.close()

    def test_ledger_requires_operation_evidence(self) -> None:
        """Reject ledger rows that do not reference a persistent operation record."""
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "rom_v2.db"
            V2Migrator(database).recreate()
            connection = sqlite3.connect(database)
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("INSERT INTO accounts VALUES ('a', 1, 'active', '2026-01-01T00:00:00Z', 60, 0)")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO crystal_ledger VALUES ('e','a','missing',1,'test','2026-01-01T00:00:00Z')")
            connection.close()


if __name__ == "__main__":
    unittest.main()
