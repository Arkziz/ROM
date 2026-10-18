"""Tests for the transaction-bound ROM V2 SQLite repository base."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rom_v2.infrastructure.persistence import (
    RepositoryContractError,
    SQLiteRepositoryBase,
    SQLiteUnitOfWork,
    V2ConnectionFactory,
    V2Migrator,
)


class AccountRepository(SQLiteRepositoryBase):
    """Provide a minimal concrete fixture without adding a production domain owner."""

    def add(self, account_id: str, telegram_user_id: int) -> None:
        """Insert one account through parameterized SQL."""
        changed = self.execute(
            "INSERT INTO accounts(account_id,telegram_user_id,status,registered_at_utc,bag_capacity,version) VALUES (?,?,?, ?,?,?)",
            (account_id, telegram_user_id, "active", "2026-01-01T00:00:00Z", 60, 0),
        )
        self.require_exact_rowcount(changed)

    def get(self, account_id: str):
        """Return one account fixture row."""
        return self.require_one("SELECT * FROM accounts WHERE account_id = ?", (account_id,))


class SQLiteRepositoryBaseTest(unittest.TestCase):
    """Verify transaction ownership, mapping, parameterization, and stale guards."""

    def _factory(self, directory: str) -> V2ConnectionFactory:
        runtime_root = Path(directory) / ".runtime" / "v2" / "db"
        database_path = runtime_root / "rom_v2.db"
        V2Migrator(database_path).recreate()
        return V2ConnectionFactory(database_path, runtime_root=runtime_root)

    def test_repository_requires_active_unit_of_work_transaction(self) -> None:
        """Reject connections not currently owned by an active Unit of Work."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            connection = factory.connect_read_write()
            with self.assertRaisesRegex(RepositoryContractError, "repository_requires_active_transaction"):
                AccountRepository(connection)
            connection.close()

    def test_repository_uses_unit_of_work_connection_and_commit(self) -> None:
        """Persist repository writes only through the Unit of Work commit point."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            with SQLiteUnitOfWork(factory) as unit:
                repository = AccountRepository(unit.connection)
                repository.add("a", 1)
                self.assertEqual(repository.get("a")["telegram_user_id"], 1)
                unit.commit()
            connection = factory.connect_read_only()
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM accounts").fetchone()[0], 1)
            connection.close()

    def test_repository_write_rolls_back_with_unit_of_work(self) -> None:
        """Prove that repository adapters do not commit independently."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            with SQLiteUnitOfWork(factory) as unit:
                AccountRepository(unit.connection).add("a", 1)
            connection = factory.connect_read_only()
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM accounts").fetchone()[0], 0)
            connection.close()

    def test_repository_rejects_use_after_transaction_terminal(self) -> None:
        """Prevent a repository from escaping its Unit of Work lifetime."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            with SQLiteUnitOfWork(factory) as unit:
                repository = AccountRepository(unit.connection)
                unit.rollback()
                with self.assertRaisesRegex(RepositoryContractError, "repository_transaction_not_active"):
                    repository.fetch_all("SELECT * FROM accounts")

    def test_require_one_and_rowcount_fail_closed(self) -> None:
        """Expose stable errors for missing rows and stale expected updates."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            with SQLiteUnitOfWork(factory) as unit:
                repository = AccountRepository(unit.connection)
                with self.assertRaisesRegex(RepositoryContractError, "repository_row_not_found"):
                    repository.get("missing")
                with self.assertRaisesRegex(RepositoryContractError, "repository_rowcount_mismatch"):
                    repository.require_exact_rowcount(0)

    def test_empty_and_multi_statement_sql_are_rejected(self) -> None:
        """Keep one repository call mapped to one auditable SQL statement."""
        with tempfile.TemporaryDirectory() as directory:
            factory = self._factory(directory)
            with SQLiteUnitOfWork(factory) as unit:
                repository = AccountRepository(unit.connection)
                with self.assertRaisesRegex(RepositoryContractError, "empty_repository_statement"):
                    repository.fetch_all("  ")
                with self.assertRaisesRegex(RepositoryContractError, "multiple_repository_statements_forbidden"):
                    repository.fetch_all("SELECT 1; SELECT 2")


if __name__ == "__main__":
    unittest.main()
