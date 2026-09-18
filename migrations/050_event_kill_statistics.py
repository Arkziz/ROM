# -*- coding: utf-8 -*-
"""Persistent exactly-once event kill statistics."""
def up(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS event_kill_receipts (
        event_key TEXT NOT NULL, terminal_event_id TEXT NOT NULL,
        user_id INTEGER NOT NULL, mob_key TEXT NOT NULL,
        recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(event_key, terminal_event_id),
        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS event_kill_statistics (
        event_key TEXT NOT NULL, user_id INTEGER NOT NULL, mob_key TEXT NOT NULL,
        kills INTEGER NOT NULL DEFAULT 0 CHECK(kills >= 0),
        first_reached_at TEXT NOT NULL, updated_at TEXT NOT NULL,
        PRIMARY KEY(event_key,user_id,mob_key),
        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_event_kill_rank ON event_kill_statistics(event_key,mob_key,kills DESC,first_reached_at ASC,user_id ASC)")
