# -*- coding: utf-8 -*-
"""Persistent World Chronicles foundation for ROM Stage 18.xx.11."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "game.db"
WORLD_CHRONICLE_RETENTION = 100
WORLD_CHRONICLE_PAGE_SIZE = 10
WORLD_CHRONICLE_EVENT_TYPES = {
    "player_joined",
    "player_level_up",
    "equipment_max_refine",
    "location_boss_defeated",
}


def _connect(db_path=None):
    connection = sqlite3.connect(str(db_path or DB_PATH), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=30000")
    return connection


def init_world_chronicle_system(db_path=None):
    connection = _connect(db_path)
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS world_chronicle_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                actor_user_id INTEGER,
                actor_name_snapshot TEXT NOT NULL,
                subject_key TEXT,
                subject_name_snapshot TEXT,
                location_id TEXT,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                deduplication_key TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS ix_world_chronicle_events_newest
            ON world_chronicle_events(created_at DESC, id DESC);
            """
        )
        connection.commit()
        return {"success": True}
    finally:
        connection.close()


def record_world_chronicle_event(
    event_type,
    actor_user_id,
    actor_name_snapshot,
    deduplication_key,
    *,
    subject_key=None,
    subject_name_snapshot=None,
    location_id=None,
    metadata=None,
    connection=None,
    db_path=None,
):
    event_type = str(event_type or "").strip()
    actor_name = str(actor_name_snapshot or "").strip()
    deduplication_key = str(deduplication_key or "").strip()
    if event_type not in WORLD_CHRONICLE_EVENT_TYPES:
        return {"success": False, "inserted": False, "reason": "invalid_event_type"}
    if not actor_name or not deduplication_key:
        return {"success": False, "inserted": False, "reason": "missing_required_value"}

    owns_connection = connection is None
    active_connection = connection or _connect(db_path)
    try:
        cursor = active_connection.execute(
            """
            INSERT OR IGNORE INTO world_chronicle_events (
                event_type, actor_user_id, actor_name_snapshot,
                subject_key, subject_name_snapshot, location_id,
                metadata_json, deduplication_key, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_type,
                int(actor_user_id) if actor_user_id is not None else None,
                actor_name,
                str(subject_key) if subject_key is not None else None,
                str(subject_name_snapshot) if subject_name_snapshot is not None else None,
                str(location_id) if location_id is not None else None,
                json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True),
                deduplication_key,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        inserted = cursor.rowcount == 1
        if inserted:
            active_connection.execute(
                """
                DELETE FROM world_chronicle_events
                WHERE id NOT IN (
                    SELECT id
                    FROM world_chronicle_events
                    ORDER BY created_at DESC, id DESC
                    LIMIT ?
                )
                """,
                (WORLD_CHRONICLE_RETENTION,),
            )
        if owns_connection:
            active_connection.commit()
        return {"success": True, "inserted": inserted}
    except Exception:
        if owns_connection:
            active_connection.rollback()
        raise
    finally:
        if owns_connection:
            active_connection.close()


def get_world_chronicle_page(page=0, page_size=WORLD_CHRONICLE_PAGE_SIZE, db_path=None):
    page = max(0, int(page or 0))
    page_size = max(1, min(WORLD_CHRONICLE_PAGE_SIZE, int(page_size or WORLD_CHRONICLE_PAGE_SIZE)))
    connection = _connect(db_path)
    try:
        total = int(connection.execute("SELECT COUNT(*) FROM world_chronicle_events").fetchone()[0])
        max_page = max(0, (total - 1) // page_size) if total else 0
        page = min(page, max_page)
        rows = connection.execute(
            """
            SELECT *
            FROM world_chronicle_events
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (page_size, page * page_size),
        ).fetchall()
        return {
            "items": [dict(row) for row in rows],
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_previous": page > 0,
            "has_next": page < max_page,
        }
    finally:
        connection.close()


def get_character_name_snapshot(user_id, connection=None, db_path=None):
    owns_connection = connection is None
    active_connection = connection or _connect(db_path)
    try:
        row = active_connection.execute(
            "SELECT TRIM(COALESCE(character_name, '')) FROM users WHERE user_id=?",
            (int(user_id),),
        ).fetchone()
        return str(row[0] if row else "").strip()
    finally:
        if owns_connection:
            active_connection.close()
