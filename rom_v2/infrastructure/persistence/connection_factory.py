"""Canonical SQLite connection factory for the isolated ROM V2 database."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

DEFAULT_BUSY_TIMEOUT_MS: Final[int] = 5_000
DEFAULT_MMAP_SIZE_BYTES: Final[int] = 134_217_728


@dataclass(frozen=True, slots=True)
class ConnectionProfile:
    """Describe observable safety settings applied to one SQLite connection."""

    database_path: Path
    mode: Literal["read_write", "read_only"]
    foreign_keys: bool
    busy_timeout_ms: int
    journal_mode: str
    synchronous: int
    query_only: bool


class V2ConnectionFactory:
    """Create configured SQLite connections only for the isolated V2 database."""

    def __init__(
        self,
        database_path: Path,
        *,
        runtime_root: Path,
        busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
    ) -> None:
        """Validate path ownership and store deterministic connection settings."""
        resolved_root = runtime_root.resolve()
        resolved_path = database_path.resolve()
        if resolved_path == resolved_root or resolved_root not in resolved_path.parents:
            raise ValueError("database_path_outside_v2_runtime_root")
        if resolved_path.name != "rom_v2.db":
            raise ValueError("invalid_v2_database_filename")
        if busy_timeout_ms < 1 or busy_timeout_ms > 60_000:
            raise ValueError("invalid_busy_timeout_ms")
        self._database_path = resolved_path
        self._runtime_root = resolved_root
        self._busy_timeout_ms = busy_timeout_ms

    @property
    def database_path(self) -> Path:
        """Return the canonical isolated V2 database path."""
        return self._database_path

    def connect_read_write(self) -> sqlite3.Connection:
        """Open a configured read/write connection without implicit transactions."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            self._database_path,
            timeout=self._busy_timeout_ms / 1_000,
            isolation_level=None,
        )
        self._configure_common(connection)
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        return connection

    def connect_read_only(self) -> sqlite3.Connection:
        """Open a query-only URI connection that cannot mutate the database."""
        connection = sqlite3.connect(
            f"file:{self._database_path.as_posix()}?mode=ro",
            uri=True,
            timeout=self._busy_timeout_ms / 1_000,
            isolation_level=None,
        )
        self._configure_common(connection)
        connection.execute("PRAGMA query_only = ON")
        return connection

    def inspect(self, connection: sqlite3.Connection, mode: Literal["read_write", "read_only"]) -> ConnectionProfile:
        """Return the effective SQLite safety profile for acceptance evidence."""
        return ConnectionProfile(
            database_path=self._database_path,
            mode=mode,
            foreign_keys=bool(connection.execute("PRAGMA foreign_keys").fetchone()[0]),
            busy_timeout_ms=int(connection.execute("PRAGMA busy_timeout").fetchone()[0]),
            journal_mode=str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower(),
            synchronous=int(connection.execute("PRAGMA synchronous").fetchone()[0]),
            query_only=bool(connection.execute("PRAGMA query_only").fetchone()[0]),
        )

    def _configure_common(self, connection: sqlite3.Connection) -> None:
        """Apply mandatory settings shared by read/write and read-only connections."""
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {self._busy_timeout_ms}")
        connection.execute("PRAGMA temp_store = MEMORY")
        connection.execute(f"PRAGMA mmap_size = {DEFAULT_MMAP_SIZE_BYTES}")
