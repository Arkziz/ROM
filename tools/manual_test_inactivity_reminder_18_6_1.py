#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Controlled manual-test helper for ROM Stage 18.6.1.

Usage from ROM root:
  python .\tools\manual_test_inactivity_reminder_18_6_1.py backup 8914495259
  python .\tools\manual_test_inactivity_reminder_18_6_1.py prepare-before 8914495259
  python .\tools\manual_test_inactivity_reminder_18_6_1.py prepare-due 8914495259
  python .\tools\manual_test_inactivity_reminder_18_6_1.py status 8914495259
  python .\tools\manual_test_inactivity_reminder_18_6_1.py restore 8914495259
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SESSION_PREFIX = "manual_inactivity_test_18_6_1"
REMINDER_COLUMNS = (
    "id",
    "user_id",
    "inactivity_started_at",
    "eligible_at",
    "attempted_at",
    "delivery_status",
    "error_type",
    "created_at",
    "updated_at",
)


def rom_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here.parent.parent, Path.cwd(), Path.cwd().parent):
        if (candidate / "db.py").is_file() and (candidate / "game.db").is_file():
            return candidate.resolve()
    raise RuntimeError("ROM root not found")


def state_path(root: Path, user_id: int) -> Path:
    return root / "backup" / f"{SESSION_PREFIX}_{user_id}.json"


def db_backup_path(root: Path, user_id: int) -> Path:
    return root / "backup" / f"{SESSION_PREFIX}_{user_id}_game.db"


def connect(root: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(root / "game.db"), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=30000")
    return connection


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def require_schema(connection: sqlite3.Connection) -> None:
    users_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(users)").fetchall()
    }
    required_users = {"user_id", "character_name", "character_class", "last_activity_at"}
    if not required_users.issubset(users_columns):
        missing = sorted(required_users - users_columns)
        raise RuntimeError(f"users schema is missing columns: {missing}")

    reminder_columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(inactivity_reminders)").fetchall()
    }
    if not set(REMINDER_COLUMNS).issubset(reminder_columns):
        missing = sorted(set(REMINDER_COLUMNS) - reminder_columns)
        raise RuntimeError(f"inactivity_reminders schema is missing columns: {missing}")


def read_user(connection: sqlite3.Connection, user_id: int) -> sqlite3.Row:
    row = connection.execute(
        """
        SELECT user_id, character_name, character_class, last_activity_at
        FROM users
        WHERE user_id=?
        """,
        (user_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("Test user was not found in users")
    if not str(row["character_name"] or "").strip():
        raise RuntimeError("Test user has no character_name")
    if not str(row["character_class"] or "").strip():
        raise RuntimeError("Test user has no character_class")
    return row


def read_reminders(connection: sqlite3.Connection, user_id: int) -> list[dict]:
    rows = connection.execute(
        "SELECT * FROM inactivity_reminders WHERE user_id=? ORDER BY id",
        (user_id,),
    ).fetchall()
    return [{column: row[column] for column in REMINDER_COLUMNS} for row in rows]


def write_state(root: Path, user_id: int, user: sqlite3.Row, reminders: list[dict]) -> None:
    root.joinpath("backup").mkdir(exist_ok=True)
    state = {
        "stage": "18.6.1",
        "user_id": user_id,
        "created_at_utc": utc_now().isoformat(),
        "original_last_activity_at": user["last_activity_at"],
        "original_reminders": reminders,
    }
    state_path(root, user_id).write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def backup(root: Path, user_id: int) -> None:
    state = state_path(root, user_id)
    if state.exists():
        raise RuntimeError(
            f"Active test backup already exists: {state.name}. Run restore first."
        )
    connection = connect(root)
    try:
        require_schema(connection)
        user = read_user(connection, user_id)
        reminders = read_reminders(connection, user_id)
    finally:
        connection.close()
    shutil.copy2(root / "game.db", db_backup_path(root, user_id))
    write_state(root, user_id, user, reminders)
    print("[PASS] Manual-test backup created")
    print(f"State: backup\\{state.name}")
    print(f"DB copy: backup\\{db_backup_path(root, user_id).name}")
    print("Original values are stored locally and were not printed")


def ensure_backup(root: Path, user_id: int) -> None:
    if not state_path(root, user_id).is_file():
        backup(root, user_id)


def set_cycle(root: Path, user_id: int, mode: str) -> None:
    ensure_backup(root, user_id)
    now = utc_now()
    if mode == "prepare-before":
        value = now - timedelta(days=7) + timedelta(seconds=1)
        expected = "INELIGIBLE for approximately one second"
    elif mode == "prepare-due":
        value = now - timedelta(days=7)
        expected = "ELIGIBLE immediately"
    else:
        raise RuntimeError(f"Unknown preparation mode: {mode}")

    stamp = value.isoformat()
    connection = connect(root)
    try:
        require_schema(connection)
        read_user(connection, user_id)
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "DELETE FROM inactivity_reminders WHERE user_id=?",
            (user_id,),
        )
        changed = connection.execute(
            "UPDATE users SET last_activity_at=? WHERE user_id=?",
            (stamp, user_id),
        ).rowcount
        if changed != 1:
            raise RuntimeError("Expected exactly one users row to be updated")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    print(f"[PASS] {mode} completed")
    print(f"Expected state: {expected}")
    print("Reminder rows for the test user were cleared for this controlled cycle")
    print("Do not send messages from the test account before the worker check")


def status(root: Path, user_id: int) -> None:
    connection = connect(root)
    try:
        require_schema(connection)
        user = read_user(connection, user_id)
        reminders = read_reminders(connection, user_id)
        quick = connection.execute("PRAGMA quick_check").fetchone()[0]
        foreign_keys = list(connection.execute("PRAGMA foreign_key_check"))
    finally:
        connection.close()

    print("[PASS] Current test state")
    print(f"User ID: {user_id}")
    print(f"Character: {user['character_name']}")
    print(f"Class: {user['character_class']}")
    print(f"last_activity_at: {user['last_activity_at']}")
    print(f"Reminder records: {len(reminders)}")
    for row in reminders:
        print(
            f"  id={row['id']} status={row['delivery_status']} "
            f"cycle={row['inactivity_started_at']} error_type={row['error_type']}"
        )
    print(f"quick_check: {quick}")
    print(f"foreign_key_violations: {len(foreign_keys)}")


def restore(root: Path, user_id: int) -> None:
    state_file = state_path(root, user_id)
    if not state_file.is_file():
        raise RuntimeError("Manual-test state backup was not found")
    state = json.loads(state_file.read_text(encoding="utf-8"))
    if int(state.get("user_id")) != user_id:
        raise RuntimeError("Backup user ID mismatch")

    connection = connect(root)
    try:
        require_schema(connection)
        read_user(connection, user_id)
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("DELETE FROM inactivity_reminders WHERE user_id=?", (user_id,))
        for row in state.get("original_reminders", []):
            placeholders = ",".join("?" for _ in REMINDER_COLUMNS)
            columns = ",".join(REMINDER_COLUMNS)
            connection.execute(
                f"INSERT INTO inactivity_reminders({columns}) VALUES({placeholders})",
                tuple(row.get(column) for column in REMINDER_COLUMNS),
            )
        changed = connection.execute(
            "UPDATE users SET last_activity_at=? WHERE user_id=?",
            (state.get("original_last_activity_at"), user_id),
        ).rowcount
        if changed != 1:
            raise RuntimeError("Expected exactly one users row to be restored")
        connection.commit()
        quick = connection.execute("PRAGMA quick_check").fetchone()[0]
        foreign_keys = list(connection.execute("PRAGMA foreign_key_check"))
        if quick != "ok" or foreign_keys:
            raise RuntimeError(
                f"Post-restore database check failed: quick={quick}, FK={len(foreign_keys)}"
            )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    state_file.unlink()
    db_copy = db_backup_path(root, user_id)
    if db_copy.exists():
        db_copy.unlink()
    print("[PASS] Original test-user state restored")
    print("Temporary state and DB copy removed")
    print("main.py may be started")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ROM Stage 18.6.1 manual-test helper")
    parser.add_argument(
        "action",
        choices=("backup", "prepare-before", "prepare-due", "status", "restore"),
    )
    parser.add_argument("user_id", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = rom_root()
    if args.user_id <= 0:
        raise RuntimeError("user_id must be positive")
    if args.action == "backup":
        backup(root, args.user_id)
    elif args.action in {"prepare-before", "prepare-due"}:
        set_cycle(root, args.user_id, args.action)
    elif args.action == "status":
        status(root, args.user_id)
    elif args.action == "restore":
        restore(root, args.user_id)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"[FAIL] {type(error).__name__}: {error}")
        print("Do not start main.py until the failure is understood or restore succeeds")
        raise SystemExit(1)
