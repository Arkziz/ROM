# -*- coding: utf-8 -*-
"""Migration 053: persistent state and isolated quest-item storage for story quests.

Only ACTIVE, COMPLETED and SKIPPED are persisted. LOCKED and AVAILABLE remain
derived states. Quest items are isolated from ordinary inventory, so they do not
consume bag slots and cannot enter vendor, trade or auction routes.
"""


def up(conn):
    """Create story-quest persistence using the runner-owned connection.

    The migration intentionally does not commit. Transaction ownership belongs
    to the canonical migration runner, which can atomically commit or roll back
    the complete migration and record it in schema_migrations.
    """

    # One row represents one started or finalized quest. The partial unique
    # index enforces the policy of one ACTIVE story quest per user.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_story_quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            quest_id TEXT NOT NULL,
            quest_number INTEGER NOT NULL CHECK (quest_number > 0),
            status TEXT NOT NULL
                CHECK (status IN ('ACTIVE', 'COMPLETED', 'SKIPPED')),
            progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0),
            target_quantity INTEGER NOT NULL DEFAULT 1
                CHECK (target_quantity > 0),
            reward_claimed INTEGER NOT NULL DEFAULT 0
                CHECK (reward_claimed IN (0, 1)),
            started_at TEXT NOT NULL,
            completed_at TEXT,
            skipped_at TEXT,
            updated_at TEXT NOT NULL,
            UNIQUE (user_id, quest_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_user_story_quests_one_active
        ON user_story_quests(user_id)
        WHERE status = 'ACTIVE'
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_user_story_quests_journal
        ON user_story_quests(user_id, quest_number, status)
        """
    )

    # Quest-item rows have no inventory_id. This structural separation prevents
    # them from entering bag-capacity, vendor, auction or player-trade routes.
    conn.execute(
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
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_user_story_quest_items_owner
        ON user_story_quest_items(user_id, quest_id)
        """
    )
