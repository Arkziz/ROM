"""ROM 10.2.0: normalized inventory rune sockets."""
from __future__ import annotations


def up(conn):
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory_runes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_id INTEGER NOT NULL,
            slot_index INTEGER NOT NULL CHECK(slot_index >= 0),
            rune_item_id INTEGER NOT NULL,
            rune_stat TEXT NOT NULL CHECK(rune_stat IN ('STR','STA','DEX','INT','WIS')),
            rune_level INTEGER NOT NULL CHECK(rune_level BETWEEN 1 AND 5),
            inserted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(inventory_id, slot_index),
            FOREIGN KEY(inventory_id) REFERENCES inventory(id) ON DELETE CASCADE,
            FOREIGN KEY(rune_item_id) REFERENCES items(id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_inventory_runes_inventory_id "
        "ON inventory_runes(inventory_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_inventory_runes_rune_item_id "
        "ON inventory_runes(rune_item_id)"
    )
