"""Canonical clean-database integrity suite for ROM V2 SQLite persistence."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rom_v2.infrastructure.persistence import (
    SQLiteRepositoryBase,
    SQLiteUnitOfWork,
    V2ConnectionFactory,
    V2Migrator,
)


@dataclass(frozen=True, slots=True)
class IntegrityCheck:
    """Describe one deterministic integrity assertion."""

    check_id: str
    status: str
    summary: str
    details: dict[str, object]


def _factory(database_path: Path) -> V2ConnectionFactory:
    """Create the canonical connection factory for one isolated test database."""
    return V2ConnectionFactory(database_path, runtime_root=database_path.parent)


def _count(factory: V2ConnectionFactory, table: str) -> int:
    """Count rows using a read-only connection and a fixed trusted table name."""
    connection = factory.connect_read_only()
    try:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    finally:
        connection.close()


def _result(check_id: str, action: Callable[[], dict[str, object]]) -> IntegrityCheck:
    """Run one check and convert exceptions into complete machine evidence."""
    try:
        details = action()
        return IntegrityCheck(check_id, "PASS", "Integrity assertion passed.", details)
    except Exception as error:
        return IntegrityCheck(
            check_id,
            "FAIL",
            f"{type(error).__name__}: {error}",
            {"exception_type": type(error).__name__, "exception": str(error)},
        )


def _clean_recreate(database_path: Path) -> dict[str, object]:
    """Verify deterministic recreation from an empty database path."""
    migrator = V2Migrator(database_path)
    first = migrator.recreate()
    first_tables = first.table_names
    first_versions = first.applied_versions
    second = migrator.recreate()
    if first_tables != second.table_names or first_versions != second.applied_versions:
        raise AssertionError("recreate_not_deterministic")
    if len(second.table_names) != 17 or second.applied_versions != (1, 2, 3):
        raise AssertionError("unexpected_baseline_shape")
    return {"table_count": len(second.table_names), "applied_versions": list(second.applied_versions)}


def _quick_and_foreign_keys(database_path: Path) -> dict[str, object]:
    """Verify quick_check, foreign_key_check, and configured FK enforcement."""
    factory = _factory(database_path)
    connection = factory.connect_read_write()
    try:
        quick = str(connection.execute("PRAGMA quick_check").fetchone()[0])
        violations = tuple(connection.execute("PRAGMA foreign_key_check"))
        foreign_keys = int(connection.execute("PRAGMA foreign_keys").fetchone()[0])
        if quick != "ok" or violations or foreign_keys != 1:
            raise AssertionError("sqlite_integrity_failed")
        return {"quick_check": quick, "foreign_key_violations": len(violations), "foreign_keys": foreign_keys}
    finally:
        connection.close()


def _unique_constraints(database_path: Path) -> dict[str, object]:
    """Verify representative account identity and event-stream uniqueness."""
    factory = _factory(database_path)
    with SQLiteUnitOfWork(factory) as unit:
        repository = SQLiteRepositoryBase(unit.connection)
        repository.execute(
            "INSERT INTO accounts VALUES (?,?,?,?,?,?)",
            ("a1", 1001, "active", "2026-01-01T00:00:00Z", 60, 0),
        )
        repository.execute(
            "INSERT INTO domain_events VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            ("e1", "created", "account", "a1", 1, 0, "2026-01-01T00:00:00Z", "{}", "c1", None, 1),
        )
        unit.commit()
    duplicate_account = False
    try:
        with SQLiteUnitOfWork(factory) as unit:
            SQLiteRepositoryBase(unit.connection).execute(
                "INSERT INTO accounts VALUES (?,?,?,?,?,?)",
                ("a2", 1001, "active", "2026-01-01T00:00:00Z", 60, 0),
            )
            unit.commit()
    except sqlite3.IntegrityError:
        duplicate_account = True
    duplicate_event = False
    try:
        with SQLiteUnitOfWork(factory) as unit:
            SQLiteRepositoryBase(unit.connection).execute(
                "INSERT INTO domain_events VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                ("e2", "updated", "account", "a1", 1, 0, "2026-01-01T00:00:01Z", "{}", "c2", None, 1),
            )
            unit.commit()
    except sqlite3.IntegrityError:
        duplicate_event = True
    if not duplicate_account or not duplicate_event:
        raise AssertionError("unique_constraint_not_enforced")
    return {"telegram_identity_unique": True, "event_stream_unique": True}


def _idempotency(database_path: Path) -> dict[str, object]:
    """Verify duplicate operation and ledger settlement keys are rejected."""
    factory = _factory(database_path)
    with SQLiteUnitOfWork(factory) as unit:
        repository = SQLiteRepositoryBase(unit.connection)
        repository.execute(
            "INSERT INTO accounts VALUES (?,?,?,?,?,?)",
            ("a1", 1001, "active", "2026-01-01T00:00:00Z", 60, 0),
        )
        repository.execute(
            "INSERT INTO operation_records VALUES (?,?,?,?,?,?,?,?)",
            ("op1", "credit", "account", "a1", "completed", "fp", "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z"),
        )
        repository.execute(
            "INSERT INTO crystal_ledger VALUES (?,?,?,?,?,?)",
            ("l1", "a1", "op1", 1, "test", "2026-01-01T00:00:01Z"),
        )
        unit.commit()
    duplicate_operation = False
    try:
        with SQLiteUnitOfWork(factory) as unit:
            SQLiteRepositoryBase(unit.connection).execute(
                "INSERT INTO operation_records VALUES (?,?,?,?,?,?,?,?)",
                ("op1", "credit", "account", "a1", "completed", "fp", "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z"),
            )
            unit.commit()
    except sqlite3.IntegrityError:
        duplicate_operation = True
    duplicate_settlement = False
    try:
        with SQLiteUnitOfWork(factory) as unit:
            SQLiteRepositoryBase(unit.connection).execute(
                "INSERT INTO crystal_ledger VALUES (?,?,?,?,?,?)",
                ("l2", "a1", "op1", 1, "test", "2026-01-01T00:00:02Z"),
            )
            unit.commit()
    except sqlite3.IntegrityError:
        duplicate_settlement = True
    if not duplicate_operation or not duplicate_settlement:
        raise AssertionError("idempotency_constraint_not_enforced")
    return {"operation_id_unique": True, "ledger_operation_unique": True}


def _rollback_and_partial_mutation(database_path: Path) -> dict[str, object]:
    """Verify exceptions and late constraint failures leave no partial mutation."""
    factory = _factory(database_path)
    before = _count(factory, "accounts")
    try:
        with SQLiteUnitOfWork(factory) as unit:
            repository = SQLiteRepositoryBase(unit.connection)
            repository.execute(
                "INSERT INTO accounts VALUES (?,?,?,?,?,?)",
                ("rollback", 2001, "active", "2026-01-01T00:00:00Z", 60, 0),
            )
            raise RuntimeError("forced_rollback")
    except RuntimeError:
        pass
    after_exception = _count(factory, "accounts")
    try:
        with SQLiteUnitOfWork(factory) as unit:
            repository = SQLiteRepositoryBase(unit.connection)
            repository.execute(
                "INSERT INTO accounts VALUES (?,?,?,?,?,?)",
                ("partial", 2002, "active", "2026-01-01T00:00:00Z", 60, 0),
            )
            repository.execute(
                "INSERT INTO characters VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("c-bad", "missing", "name", "class", 1, 0, "start", 10, None, 0),
            )
            unit.commit()
    except sqlite3.IntegrityError:
        pass
    after_constraint = _count(factory, "accounts")
    if before != after_exception or before != after_constraint:
        raise AssertionError("partial_mutation_remained")
    return {"before": before, "after_exception": after_exception, "after_constraint": after_constraint}


def _restart_recovery(database_path: Path) -> dict[str, object]:
    """Verify committed state and integrity survive connection/process-style restart."""
    factory = _factory(database_path)
    with SQLiteUnitOfWork(factory) as unit:
        SQLiteRepositoryBase(unit.connection).execute(
            "INSERT INTO accounts VALUES (?,?,?,?,?,?)",
            ("restart", 3001, "active", "2026-01-01T00:00:00Z", 60, 0),
        )
        unit.commit()
    del factory
    reopened = _factory(database_path)
    connection = reopened.connect_read_only()
    try:
        count = int(connection.execute("SELECT COUNT(*) FROM accounts WHERE account_id = ?", ("restart",)).fetchone()[0])
        quick = str(connection.execute("PRAGMA quick_check").fetchone()[0])
        violations = len(tuple(connection.execute("PRAGMA foreign_key_check")))
    finally:
        connection.close()
    if count != 1 or quick != "ok" or violations:
        raise AssertionError("restart_recovery_failed")
    return {"committed_row_found": True, "quick_check": quick, "foreign_key_violations": violations}


def run_suite(workspace: Path) -> dict[str, object]:
    """Run the complete suite with clean isolated databases per check group."""
    workspace.mkdir(parents=True, exist_ok=True)
    plans: tuple[tuple[str, Callable[[Path], dict[str, object]]], ...] = (
        ("CLEAN_RECREATE", _clean_recreate),
        ("QUICK_AND_FOREIGN_KEYS", _quick_and_foreign_keys),
        ("UNIQUE_CONSTRAINTS", _unique_constraints),
        ("IDEMPOTENCY", _idempotency),
        ("ROLLBACK_PARTIAL_MUTATION", _rollback_and_partial_mutation),
        ("RESTART_RECOVERY", _restart_recovery),
    )
    checks: list[IntegrityCheck] = []
    for check_id, action in plans:
        database_path = workspace / check_id.lower() / "rom_v2.db"
        V2Migrator(database_path).recreate()
        checks.append(_result(check_id, lambda path=database_path, task=action: task(path)))
    failures = [check.check_id for check in checks if check.status != "PASS"]
    return {
        "status": "PASS" if not failures else "FAIL",
        "check_count": len(checks),
        "failed_checks": failures,
        "checks": [asdict(check) for check in checks],
    }


def main() -> int:
    """Run the suite using a temporary workspace or a caller-provided directory."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace")
    parser.add_argument("--json-out")
    args = parser.parse_args()
    if args.workspace:
        result = run_suite(Path(args.workspace))
    else:
        with tempfile.TemporaryDirectory(prefix="rom-v2-integrity-") as directory:
            result = run_suite(Path(directory))
    if args.json_out:
        output = Path(args.json_out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ROM V2 DB integrity suite: {result['status']}")
    for check in result["checks"]:
        print(f"[{check['status']}] {check['check_id']}: {check['summary']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
