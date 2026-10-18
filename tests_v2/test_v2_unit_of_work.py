"""Tests for the explicit transactional ROM V2 SQLite Unit of Work."""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from rom_v2.infrastructure.persistence import (
    SQLiteUnitOfWork,
    V2ConnectionFactory,
    V2Migrator,
)


class SQLiteUnitOfWorkTest(unittest.TestCase):
    """Verify commit, rollback, exception, one-shot, and atomicity behavior."""

    def _factory(self, directory: str) -> V2ConnectionFactory:
        runtime_root = Path(directory) / ".runtime" / "v2" / "db"
        database_path = runtime_root / "rom_v2.db"
        V2Migrator(database_path).recreate()
        return V2ConnectionFactory(database_path, runtime_root=runtime_root)

    def _account_count(self, factory: V2ConnectionFactory) -> int:
        connection = factory.connect_read_only()
        try:
            return int(connection.execute("SELECT COUNT(*) FROM accounts").fetchone()[0])
        finally:
            connection.close()

    def test_explicit_commit_persists_one_atomic_operation(self) -> None:
        """Persist account, operation, and ledger rows through one commit point."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            with SQLiteUnitOfWork(factory) as unit:
                unit.connection.execute(
                    "INSERT INTO accounts VALUES ('a',1,'active','2026-01-01T00:00:00Z',60,0)"
                )
                unit.connection.execute(
                    "INSERT INTO operation_records VALUES ('o','credit','account','a','completed','fp','2026-01-01T00:00:00Z','2026-01-01T00:00:00Z')"
                )
                unit.connection.execute(
                    "INSERT INTO crystal_ledger VALUES ('e','a','o',1,'test','2026-01-01T00:00:00Z')"
                )
                unit.commit()
            self.assertTrue(unit.committed)
            self.assertEqual(self._account_count(factory), 1)

    def test_missing_commit_rolls_back(self) -> None:
        """Rollback a technically successful block that omitted explicit commit."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            with SQLiteUnitOfWork(factory) as unit:
                unit.connection.execute(
                    "INSERT INTO accounts VALUES ('a',1,'active','2026-01-01T00:00:00Z',60,0)"
                )
            self.assertFalse(unit.committed)
            self.assertEqual(self._account_count(factory), 0)

    def test_exception_rolls_back_and_propagates(self) -> None:
        """Rollback all writes and preserve the original exception."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            with self.assertRaisesRegex(RuntimeError, "boom"):
                with SQLiteUnitOfWork(factory) as unit:
                    unit.connection.execute(
                        "INSERT INTO accounts VALUES ('a',1,'active','2026-01-01T00:00:00Z',60,0)"
                    )
                    raise RuntimeError("boom")
            self.assertEqual(self._account_count(factory), 0)

    def test_explicit_rollback_is_terminal(self) -> None:
        """Prevent mutation after rollback and keep the database unchanged."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            with SQLiteUnitOfWork(factory) as unit:
                unit.connection.execute(
                    "INSERT INTO accounts VALUES ('a',1,'active','2026-01-01T00:00:00Z',60,0)"
                )
                unit.rollback()
                with self.assertRaisesRegex(RuntimeError, "unit_of_work_not_active"):
                    _ = unit.connection
            self.assertEqual(self._account_count(factory), 0)

    def test_reentry_and_reuse_are_forbidden(self) -> None:
        """Keep one Unit of Work instance bound to one transaction lifetime."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            unit = SQLiteUnitOfWork(factory)
            with unit:
                with self.assertRaisesRegex(RuntimeError, "unit_of_work_reentry_forbidden"):
                    unit.__enter__()
                unit.commit()
            with self.assertRaisesRegex(RuntimeError, "unit_of_work_reentry_forbidden"):
                unit.__enter__()

    def test_database_constraint_failure_rolls_back_prior_writes(self) -> None:
        """Preserve atomicity when a later statement violates a constraint."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            with self.assertRaises(sqlite3.IntegrityError):
                with SQLiteUnitOfWork(factory) as unit:
                    unit.connection.execute(
                        "INSERT INTO accounts VALUES ('a',1,'active','2026-01-01T00:00:00Z',60,0)"
                    )
                    unit.connection.execute(
                        "INSERT INTO characters VALUES ('c','missing','name','class',1,0,'start',10,NULL,0)"
                    )
                    unit.commit()
            self.assertEqual(self._account_count(factory), 0)


if __name__ == "__main__":
    unittest.main()
