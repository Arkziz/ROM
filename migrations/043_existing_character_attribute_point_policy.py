#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM migration 043: one-time Attribute Point Policy C for existing characters."""
from __future__ import annotations
from datetime import datetime, timezone
POINTS_PER_LEVEL = 5
REQUIRED_COLUMNS = {
    "user_id", "level", "free_attribute_points",
    "total_attribute_points_earned", "allocated_strength",
    "allocated_dexterity", "allocated_intelligence",
    "allocated_wisdom", "allocated_stamina",
    "attribute_points_migrated_at",
}
def _columns(conn):
    return {str(row[1]) for row in conn.execute("PRAGMA table_info(users)")}
def up(conn):
    missing = sorted(REQUIRED_COLUMNS - _columns(conn))
    if missing:
        raise RuntimeError(f"Migration 043 missing required columns: {missing}")
    timestamp = datetime.now(timezone.utc).isoformat()
    rows = conn.execute("""SELECT user_id, COALESCE(level,1),
        COALESCE(free_attribute_points,0), COALESCE(total_attribute_points_earned,0),
        COALESCE(allocated_strength,0), COALESCE(allocated_dexterity,0),
        COALESCE(allocated_intelligence,0), COALESCE(allocated_wisdom,0),
        COALESCE(allocated_stamina,0)
        FROM users WHERE attribute_points_migrated_at IS NULL
           OR TRIM(attribute_points_migrated_at)='' ORDER BY user_id""").fetchall()
    migrated = compensated = excess = 0
    points_added = 0
    for row in rows:
        user_id, level, free_points, earned, a_str, a_dex, a_int, a_wis, a_sta = map(int, row)
        allocated = a_str + a_dex + a_int + a_wis + a_sta
        if earned != free_points + allocated:
            raise RuntimeError(
                f"Migration 043 invariant failed before migration for user {user_id}: "
                f"earned={earned}, free={free_points}, allocated={allocated}"
            )
        expected_total = max(0, level - 1) * POINTS_PER_LEVEL
        missing_points = max(0, expected_total - earned)
        if earned > expected_total:
            excess += 1
        if missing_points:
            compensated += 1
            points_added += missing_points
        conn.execute("""UPDATE users SET
            free_attribute_points=free_attribute_points+?,
            total_attribute_points_earned=total_attribute_points_earned+?,
            attribute_points_migrated_at=?
            WHERE user_id=? AND (attribute_points_migrated_at IS NULL
                OR TRIM(attribute_points_migrated_at)='')""",
            (missing_points, missing_points, timestamp, user_id),
        )
        if conn.execute("SELECT changes()").fetchone()[0] != 1:
            raise RuntimeError(f"Migration 043 concurrent/idempotency update failed for user {user_id}")
        migrated += 1
    invalid = conn.execute("""SELECT COUNT(*) FROM users WHERE
        total_attribute_points_earned != free_attribute_points
          + allocated_strength + allocated_dexterity + allocated_intelligence
          + allocated_wisdom + allocated_stamina""").fetchone()[0]
    if invalid:
        raise RuntimeError(f"Migration 043 post-invariant violations: {invalid}")
    unmarked = conn.execute("""SELECT COUNT(*) FROM users WHERE
        attribute_points_migrated_at IS NULL OR TRIM(attribute_points_migrated_at)=''""").fetchone()[0]
    if unmarked:
        raise RuntimeError(f"Migration 043 unmarked users after migration: {unmarked}")
    return {"migrated":migrated,"compensated":compensated,
            "points_added":points_added,"excess_preserved":excess}
