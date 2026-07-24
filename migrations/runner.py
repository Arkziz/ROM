"""
ROM migrations foundation.

Refactor 9.0.11.

Purpose:
- Provide a safe migration runner for future DB schema changes.
- Track applied migrations in schema_migrations table.
- Keep existing init_db() behavior unchanged for now.

Migration file format:
    migrations/001_example.py

Each migration may expose either:
    def up(conn): ...

or:
    def migrate(conn): ...

The function receives sqlite3 connection and should use conn.execute(...).
The runner commits after each successful migration and records it.
"""

from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path
from typing import Callable, Iterable

MIGRATIONS_TABLE = "schema_migrations"


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {MIGRATIONS_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_name TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def get_applied_migrations(conn: sqlite3.Connection) -> set[str]:
    ensure_migrations_table(conn)
    rows = conn.execute(
        f"SELECT migration_name FROM {MIGRATIONS_TABLE} ORDER BY migration_name"
    ).fetchall()
    return {row[0] for row in rows}


def discover_migration_files(migrations_dir: Path | None = None) -> list[Path]:
    if migrations_dir is None:
        migrations_dir = get_project_root() / "migrations"

    if not migrations_dir.exists():
        migrations_dir.mkdir(parents=True, exist_ok=True)

    files = []
    for path in migrations_dir.glob("*.py"):
        if path.name.startswith("__"):
            continue
        if path.name in {"runner.py", "README.md"}:
            continue
        files.append(path)

    return sorted(files, key=lambda p: p.name)


def load_migration_callable(path: Path) -> Callable[[sqlite3.Connection], None]:
    module_name = f"rom_migration_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load migration: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if hasattr(module, "up"):
        return getattr(module, "up")

    if hasattr(module, "migrate"):
        return getattr(module, "migrate")

    raise RuntimeError(f"Migration {path.name} must define up(conn) or migrate(conn)")


def mark_migration_applied(conn: sqlite3.Connection, migration_name: str) -> None:
    conn.execute(
        f"INSERT OR IGNORE INTO {MIGRATIONS_TABLE} (migration_name) VALUES (?)",
        (migration_name,),
    )
    conn.commit()


def run_pending_migrations(conn: sqlite3.Connection, migrations_dir: Path | None = None) -> dict:
    """Run pending migrations. Returns a diagnostics dict."""

    ensure_migrations_table(conn)
    applied = get_applied_migrations(conn)
    files = discover_migration_files(migrations_dir)

    result = {
        "success": True,
        "applied": [],
        "skipped": [],
        "failed": None,
        "total_files": len(files),
    }

    for path in files:
        migration_name = path.name

        if migration_name in applied:
            result["skipped"].append(migration_name)
            continue

        try:
            migration_func = load_migration_callable(path)
            migration_func(conn)
            conn.commit()
            mark_migration_applied(conn, migration_name)
            result["applied"].append(migration_name)
        except Exception as error:
            conn.rollback()
            result["success"] = False
            result["failed"] = {
                "migration": migration_name,
                "error": str(error),
            }
            raise

    return result


def get_migration_status(conn: sqlite3.Connection, migrations_dir: Path | None = None) -> dict:
    ensure_migrations_table(conn)
    applied = get_applied_migrations(conn)
    files = discover_migration_files(migrations_dir)

    known = [path.name for path in files]
    pending = [name for name in known if name not in applied]

    return {
        "known": known,
        "applied": sorted(applied),
        "pending": pending,
        "applied_count": len(applied),
        "pending_count": len(pending),
    }
