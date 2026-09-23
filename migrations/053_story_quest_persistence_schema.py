# -*- coding: utf-8 -*-
"""Migration 053: persistent state and isolated quest-item storage for story quests.

Only ACTIVE, COMPLETED and SKIPPED are persisted. LOCKED and AVAILABLE remain
read-only derived states calculated from level, predecessor and active-quest
state. Quest items are deliberately isolated from ordinary inventory so they do
not consume bag slots and cannot enter vendor, trade or auction routes.
"""
from db_modules.connection import conn, cursor


# Persist one row per started/finalized quest. The partial unique index enforces
# the Stage 19 contract that one character cannot have two ACTIVE story quests.
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS user_story_quests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        quest_id TEXT NOT NULL,
        quest_number INTEGER NOT NULL CHECK (quest_number > 0),
        status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'COMPLETED', 'SKIPPED')),
        progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0),
        target_quantity INTEGER NOT NULL DEFAULT 1 CHECK (target_quantity > 0),
        reward_claimed INTEGER NOT NULL DEFAULT 0 CHECK (reward_claimed IN (0, 1)),
        started_at TEXT NOT NULL,
        completed_at TEXT,
        skipped_at TEXT,
        updated_at TEXT NOT NULL,
        UNIQUE (user_id, quest_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    """
)

cursor.execute(
    """
    CREATE UNIQUE INDEX IF NOT EXISTS ux_user_story_quests_one_active
    ON user_story_quests(user_id)
    WHERE status = 'ACTIVE'
    """
)

cursor.execute(
    """
    CREATE INDEX IF NOT EXISTS ix_user_story_quests_journal
    ON user_story_quests(user_id, quest_number, status)
    """
)

# Quest item quantities are scoped by both quest and stable item key. They have
# no inventory_id and therefore cannot leak into ordinary economic operations.
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS user_story_quest_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        quest_id TEXT NOT NULL,
        item_key TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
        updated_at TEXT NOT NULL,
        UNIQUE (user_id, quest_id, item_key),
        FOREIGN KEY (user_id, quest_id)
            REFERENCES user_story_quests(user_id, quest_id)
            ON DELETE CASCADE
    )
    """
)

cursor.execute(
    """
    CREATE INDEX IF NOT EXISTS ix_user_story_quest_items_owner
    ON user_story_quest_items(user_id, quest_id)
    """
)

conn.commit()
