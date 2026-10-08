# -*- coding: utf-8 -*-
"""Migration 054: reconcile ACTIVE KILL_REGION snapshots after Stage 19.34.5."""
TARGETS = {12: 8, 17: 10, 32: 8, 36: 10, 39: 10, 42: 8, 45: 10}

def up(conn):
    """Update only ACTIVE snapshots; never finalize quests or issue rewards."""
    for quest_number, target in sorted(TARGETS.items()):
        conn.execute(
            """UPDATE user_story_quests
               SET target_quantity=?, progress=MIN(progress, ?), updated_at=updated_at
               WHERE quest_number=? AND status='ACTIVE'""",
            (int(target), int(target), int(quest_number)),
        )
