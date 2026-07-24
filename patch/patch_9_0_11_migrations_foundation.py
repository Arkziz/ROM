from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_11_migrations_foundation"
DB_MARKER = "# ✅ REFACTOR 9.0.11: MIGRATIONS FOUNDATION"
MAIN_MARKER = "# ✅ REFACTOR 9.0.11: RUN MIGRATIONS ON STARTUP"

MIGRATION_RUNNER_CODE = r'''"""
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
'''

MIGRATION_000_README = r'''# ROM migrations

This directory contains database migrations for future schema changes.

## Naming

Use numeric prefixes:

```text
001_base.py
002_equipment.py
003_classes.py
004_refine.py
005_guilds.py
006_auction.py
007_next_feature.py
```

## Migration format

Each migration file should define one function:

```python
def up(conn):
    conn.execute("ALTER TABLE users ADD COLUMN example TEXT DEFAULT ''")
```

or:

```python
def migrate(conn):
    conn.execute("ALTER TABLE users ADD COLUMN example TEXT DEFAULT ''")
```

The runner commits after each successful migration and records it in `schema_migrations`.

## Rule

Future DB schema changes should go here instead of being scattered across `db.py` or handlers.
'''

MIGRATION_EXAMPLE_CODE = r'''"""
000 migration runner smoke test placeholder.

This file intentionally does not modify game tables.
It only confirms that the migration runner can load migration modules.
"""


def up(conn):
    # No-op placeholder.
    # Keep this migration applied so the runner path is validated.
    return None
'''

TOOLS_CODE = r'''#!/usr/bin/env python3
"""Show ROM migration status."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db
from migrations.runner import get_migration_status


def main():
    status = get_migration_status(db.conn)
    print("ROM migration status")
    print("====================")
    print(f"Known:   {len(status['known'])}")
    print(f"Applied: {status['applied_count']}")
    print(f"Pending: {status['pending_count']}")
    print("")

    if status["pending"]:
        print("Pending migrations:")
        for name in status["pending"]:
            print(f"- {name}")
    else:
        print("No pending migrations.")


if __name__ == "__main__":
    main()
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def write_file(root, rel_path, content):
    target = root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if target.exists():
        backup = make_backup(root, target)
    target.write_text(content, encoding="utf-8")
    return target, backup


def patch_db(root):
    target = root / "db.py"
    if not target.exists():
        raise SystemExit("❌ db.py не знайдено.")

    original = target.read_text(encoding="utf-8")
    if DB_MARKER in original:
        return target, None, False

    backup = make_backup(root, target)
    block = r'''

# ==============================
# ✅ REFACTOR 9.0.11: MIGRATIONS FOUNDATION
# ==============================


def init_migration_system():
    from migrations.runner import ensure_migrations_table
    ensure_migrations_table(conn)
    return True


def run_pending_migrations():
    from migrations.runner import run_pending_migrations as _run
    return _run(conn)


def get_migration_status():
    from migrations.runner import get_migration_status as _status
    return _status(conn)
'''
    target.write_text(original.rstrip() + "\n" + block + "\n", encoding="utf-8")
    return target, backup, True


def patch_main(root):
    target = root / "main.py"
    if not target.exists():
        raise SystemExit("❌ main.py не знайдено.")

    original = target.read_text(encoding="utf-8")
    if MAIN_MARKER in original:
        return target, None, False

    backup = make_backup(root, target)
    text = original

    # Ensure imports are not required; call through db facade.
    call_block = r'''
# ==============================
# ✅ REFACTOR 9.0.11: RUN MIGRATIONS ON STARTUP
# ==============================
try:
    import db as _rom_db_for_migrations
    _migration_result = _rom_db_for_migrations.run_pending_migrations()
    if _migration_result.get("applied"):
        print(f"✅ DB MIGRATIONS APPLIED: {_migration_result.get('applied')}")
except Exception as migration_error:
    print(f"⚠️ DB migrations skipped/error: {migration_error}")
'''

    # Insert after init_db() call if present, otherwise before handler registration.
    if "init_db()" in text:
        text = text.replace("init_db()", "init_db()\n" + call_block, 1)
    else:
        anchor = "register_start_handlers(bot)"
        if anchor in text:
            text = text.replace(anchor, call_block + "\n" + anchor, 1)
        else:
            text = text.rstrip() + "\n" + call_block + "\n"

    target.write_text(text, encoding="utf-8")
    return target, backup, True


def patch_check_imports(root):
    target = root / "tools" / "check_imports.py"
    if not target.exists():
        return None, None, False

    original = target.read_text(encoding="utf-8")
    text = original
    changed = False

    if '"migrations/runner.py"' not in text and "'migrations/runner.py'" not in text:
        marker = '"data/balance.py",'
        if marker in text:
            text = text.replace(marker, marker + '\n    "migrations/runner.py",', 1)
            changed = True

    if '"migrations.runner"' not in text and "'migrations.runner'" not in text:
        marker = '"data.balance",'
        if marker in text:
            text = text.replace(marker, marker + '\n    "migrations.runner",', 1)
            changed = True

    if not changed:
        return target, None, False

    backup = make_backup(root, target)
    target.write_text(text, encoding="utf-8")
    return target, backup, True


def main():
    root = Path(__file__).resolve().parents[1]
    changed = []
    backups = []

    try:
        for rel_path, content in [
            ("migrations/__init__.py", '"""ROM database migrations package."""\n'),
            ("migrations/runner.py", MIGRATION_RUNNER_CODE),
            ("migrations/000_runner_smoke_test.py", MIGRATION_EXAMPLE_CODE),
            ("migrations/README.md", MIGRATION_000_README),
            ("tools/migration_status.py", TOOLS_CODE),
        ]:
            path, backup = write_file(root, rel_path, content)
            changed.append(path)
            if backup:
                backups.append(backup)

        for patcher in [patch_db, patch_main, patch_check_imports]:
            path, backup, did_change = patcher(root)
            if did_change:
                changed.append(path)
            if backup:
                backups.append(backup)

        for rel_path in [
            "migrations/__init__.py",
            "migrations/runner.py",
            "migrations/000_runner_smoke_test.py",
            "tools/migration_status.py",
            "db.py",
            "main.py",
            "tools/check_imports.py",
        ]:
            path = root / rel_path
            if path.exists() and path.suffix == ".py":
                py_compile.compile(str(path), doraise=True)

    except Exception as error:
        raise SystemExit(
            "❌ Помилка під час patch_9_0_11_migrations_foundation.\n"
            "За потреби відкотись із backup у ROM\\backup.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.11 Migrations Foundation застосовано успішно.")
    print()
    print("Створено/оновлено:")
    for path in changed:
        print(f"- {path}")

    if backups:
        print()
        print("Backup:")
        for path in backups:
            print(f"- {path}")

    print()
    print("Що додано:")
    print("- migrations/runner.py")
    print("- schema_migrations table")
    print("- run_pending_migrations() facade у db.py")
    print("- автоматичний запуск pending migrations при старті main.py")
    print("- tools/migration_status.py")
    print("- 000_runner_smoke_test.py no-op migration")
    print()
    print("Після патча запусти:")
    print("python -m py_compile .\\migrations\\runner.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\main.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")
    print("python tools/migration_status.py")
    print("python -c \"import db; print(db.run_pending_migrations()); print(db.get_migration_status())\"")


if __name__ == "__main__":
    main()
