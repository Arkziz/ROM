"""Tests for the canonical ROM V2 SQLite connection factory."""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from rom_v2.infrastructure.persistence import V2ConnectionFactory, V2Migrator


class V2ConnectionFactoryTest(unittest.TestCase):
    """Verify path isolation, SQLite pragmas, row mapping, and transaction semantics."""

    def _factory(self, directory: str) -> V2ConnectionFactory:
        runtime_root = Path(directory) / ".runtime" / "v2" / "db"
        database_path = runtime_root / "rom_v2.db"
        V2Migrator(database_path).recreate()
        return V2ConnectionFactory(database_path, runtime_root=runtime_root)

    def test_read_write_profile_is_safe_and_explicit(self) -> None:
        """Require WAL, FK enforcement, timeout, rows, and no implicit transaction."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            connection = factory.connect_read_write()
            profile = factory.inspect(connection, "read_write")
            self.assertTrue(profile.foreign_keys)
            self.assertEqual(profile.busy_timeout_ms, 5_000)
            self.assertEqual(profile.journal_mode, "wal")
            self.assertEqual(profile.synchronous, 1)
            self.assertFalse(profile.query_only)
            self.assertIs(connection.row_factory, sqlite3.Row)
            self.assertIsNone(connection.isolation_level)
            connection.close()

    def test_read_only_connection_rejects_mutation(self) -> None:
        """Open with URI mode=ro and enforce query_only defense in depth."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            connection = factory.connect_read_only()
            profile = factory.inspect(connection, "read_only")
            self.assertTrue(profile.foreign_keys)
            self.assertTrue(profile.query_only)
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("INSERT INTO accounts VALUES ('a',1,'active','2026-01-01T00:00:00Z',60,0)")
            connection.close()

    def test_factory_rejects_paths_outside_runtime_root(self) -> None:
        """Prevent accidental V1 database ownership or arbitrary SQLite access."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime_root = root / ".runtime" / "v2" / "db"
            with self.assertRaisesRegex(ValueError, "database_path_outside_v2_runtime_root"):
                V2ConnectionFactory(root / "game.db", runtime_root=runtime_root)
            with self.assertRaisesRegex(ValueError, "invalid_v2_database_filename"):
                V2ConnectionFactory(runtime_root / "other.db", runtime_root=runtime_root)

    def test_foreign_keys_are_enforced_on_every_connection(self) -> None:
        """Reject orphan rows through the factory-owned connection policy."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            connection = factory.connect_read_write()
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO characters VALUES ('c','missing','name','class',1,0,'start',10,NULL,0)"
                )
            connection.close()


if __name__ == "__main__":
    unittest.main()
