"""Reset-first migration runner for the isolated ROM V2 SQLite database."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from rom_v2.infrastructure.persistence.migrations import MIGRATIONS


@dataclass(frozen=True, slots=True)
class MigrationResult:
    """Describe deterministic migration application evidence."""

    database_path: Path
    applied_versions: tuple[int, ...]
    table_names: tuple[str, ...]
    foreign_key_violations: tuple[tuple[object, ...], ...]
    quick_check: str


class V2Migrator:
    """Create or recreate only the isolated V2 database from ordered migrations."""

    def __init__(self, database_path: Path) -> None:
        """Bind the migrator to a file below the caller-owned V2 runtime root."""
        self._database_path = database_path.resolve()

    def recreate(self) -> MigrationResult:
        """Delete only the isolated V2 database and apply every migration exactly once."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._delete_v2_database_files()
        connection = sqlite3.connect(self._database_path)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = DELETE")
            connection.execute("BEGIN IMMEDIATE")
            for migration in MIGRATIONS:
                connection.executescript(migration.sql)
                connection.execute(
                    "INSERT INTO schema_migrations(version, migration_key, applied_at_utc, checksum) VALUES (?, ?, ?, ?)",
                    (
                        migration.version,
                        migration.key,
                        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                        migration.checksum,
                    ),
                )
            connection.commit()
            return self._inspect(connection)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def verify_existing(self) -> MigrationResult:
        """Verify an existing isolated V2 database without applying migrations."""
        connection = sqlite3.connect(f"file:{self._database_path.as_posix()}?mode=ro", uri=True)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            return self._inspect(connection)
        finally:
            connection.close()

    def _inspect(self, connection: sqlite3.Connection) -> MigrationResult:
        """Collect schema, migration, integrity, and FK evidence."""
        tables = tuple(
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        )
        versions = tuple(row[0] for row in connection.execute("SELECT version FROM schema_migrations ORDER BY version"))
        violations = tuple(tuple(row) for row in connection.execute("PRAGMA foreign_key_check"))
        quick_check = str(connection.execute("PRAGMA quick_check").fetchone()[0])
        return MigrationResult(
            database_path=self._database_path,
            applied_versions=versions,
            table_names=tables,
            foreign_key_violations=violations,
            quick_check=quick_check,
        )

    def _delete_v2_database_files(self) -> None:
        """Delete only V2 DB sidecars; V1 game.db WAL/SHM are outside this ownership boundary."""
        for suffix in ("", "-wal", "-shm", "-journal"):
            candidate = Path(f"{self._database_path}{suffix}")
            candidate.unlink(missing_ok=True)
