"""Transaction-bound repository primitives for ROM V2 SQLite adapters."""
from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias

SQLParameters: TypeAlias = Sequence[object] | Mapping[str, object]


class RepositoryContractError(RuntimeError):
    """Expose a stable machine-readable repository contract failure."""

    def __init__(self, code: str) -> None:
        """Store the stable failure code without presentation coupling."""
        super().__init__(code)
        self.code = code


class SQLiteRepositoryBase:
    """Execute parameterized SQL on one active Unit of Work connection."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Bind the repository to an already-active explicit transaction."""
        if not connection.in_transaction:
            raise RepositoryContractError("repository_requires_active_transaction")
        if connection.row_factory is not sqlite3.Row:
            raise RepositoryContractError("repository_requires_row_factory")
        self._connection = connection

    @property
    def connection(self) -> sqlite3.Connection:
        """Return the transaction-owned connection after lifecycle validation."""
        self._require_active_transaction()
        return self._connection

    def execute(self, statement: str, parameters: SQLParameters = ()) -> int:
        """Execute one parameterized mutation and return its affected row count."""
        self._validate_statement(statement)
        self._require_active_transaction()
        cursor = self._connection.execute(statement, parameters)
        try:
            return int(cursor.rowcount)
        finally:
            cursor.close()

    def fetch_one(
        self,
        statement: str,
        parameters: SQLParameters = (),
    ) -> sqlite3.Row | None:
        """Return zero or one mapped row without controlling the transaction."""
        self._validate_statement(statement)
        self._require_active_transaction()
        cursor = self._connection.execute(statement, parameters)
        try:
            return cursor.fetchone()
        finally:
            cursor.close()

    def fetch_all(
        self,
        statement: str,
        parameters: SQLParameters = (),
    ) -> tuple[sqlite3.Row, ...]:
        """Return an immutable snapshot of all mapped rows."""
        self._validate_statement(statement)
        self._require_active_transaction()
        cursor = self._connection.execute(statement, parameters)
        try:
            return tuple(cursor.fetchall())
        finally:
            cursor.close()

    def require_one(
        self,
        statement: str,
        parameters: SQLParameters = (),
    ) -> sqlite3.Row:
        """Return one row or raise a stable not-found contract error."""
        row = self.fetch_one(statement, parameters)
        if row is None:
            raise RepositoryContractError("repository_row_not_found")
        return row

    def require_exact_rowcount(self, actual: int, expected: int = 1) -> None:
        """Reject stale or unexpectedly broad mutations before Unit of Work commit."""
        if expected < 0:
            raise RepositoryContractError("invalid_expected_rowcount")
        if actual != expected:
            raise RepositoryContractError("repository_rowcount_mismatch")

    def _require_active_transaction(self) -> None:
        """Fail closed if the Unit of Work transaction is no longer active."""
        if not self._connection.in_transaction:
            raise RepositoryContractError("repository_transaction_not_active")

    @staticmethod
    def _validate_statement(statement: str) -> None:
        """Reject empty and multi-statement SQL at the repository boundary."""
        normalized = statement.strip()
        if not normalized:
            raise RepositoryContractError("empty_repository_statement")
        if ";" in normalized.rstrip(";"):
            raise RepositoryContractError("multiple_repository_statements_forbidden")
