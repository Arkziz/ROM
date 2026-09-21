#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical immutable account registration timestamp."""
from datetime import datetime, timezone

MIGRATION_ID = "052_registration_date_pipeline"

def _utc_now():
    return datetime.now(timezone.utc).isoformat()

def migrate(conn):
    columns={str(row[1]) for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "registered_at" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN registered_at TEXT DEFAULT ''")
    # Legacy policy: exact historical creation time is unknowable. Existing rows
    # receive the migration time as the start of canonical registration tracking.
    legacy_timestamp=_utc_now()
    conn.execute("UPDATE users SET registered_at=? WHERE registered_at IS NULL OR TRIM(registered_at)=''",(legacy_timestamp,))
    return {"success":True,"legacy_backfill_policy":"migration_timestamp_utc"}
