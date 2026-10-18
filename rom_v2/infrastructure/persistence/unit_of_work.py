"""Explicit SQLite Unit of Work for atomic ROM V2 business operations."""
from __future__ import annotations

import sqlite3
from types import TracebackType
from typing import Final

from rom_v2.infrastructure.persistence.connection_factory import V2ConnectionFactory

_BEGIN_SQL: Final[str] = "BEGIN IMMEDIATE"


class SQLiteUnitOfWork:
    """Own exactly one connection, transaction, and terminal outcome."""

    def __init__(self, connection_factory: V2ConnectionFactory) -> None:
        """Store the canonical connection factory without opening SQLite."""
        self._connection_factory = connection_factory
        self._connection: sqlite3.Connection | None = None
        self._entered = False
        self._completed = False
        self._committed = False

    @property
    def connection(self) -> sqlite3.Connection:
        """Return the active transaction connection or fail closed."""
        if self._connection is None or not self._entered or self._completed:
            raise RuntimeError("unit_of_work_not_active")
        return self._connection

    @property
    def committed(self) -> bool:
        """Report whether the one terminal outcome was an explicit commit."""
        return self._committed

    def __enter__(self) -> SQLiteUnitOfWork:
        """Open one connection and begin one immediate transaction."""
        if self._entered:
            raise RuntimeError("unit_of_work_reentry_forbidden")
        if self._completed:
            raise RuntimeError("unit_of_work_reuse_forbidden")
        self._connection = self._connection_factory.connect_read_write()
        try:
            self._connection.execute(_BEGIN_SQL)
        except Exception:
            self._connection.close()
            self._connection = None
            raise
        self._entered = True
        return self

    def commit(self) -> None:
        """Commit exactly once and mark the Unit of Work terminal."""
        connection = self.connection
        connection.commit()
        self._committed = True
        self._completed = True

    def rollback(self) -> None:
        """Rollback exactly once and mark the Unit of Work terminal."""
        connection = self.connection
        connection.rollback()
        self._committed = False
        self._completed = True

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Rollback every non-committed path, close once, and propagate errors."""
        del exception, traceback
        connection = self._connection
        if connection is None:
            return False
        try:
            if not self._completed:
                connection.rollback()
                self._completed = True
                self._committed = False
            elif exception_type is not None and self._committed:
                # A committed operation is terminal; later presentation failures do not undo it.
                pass
        finally:
            connection.close()
            self._connection = None
        return False
