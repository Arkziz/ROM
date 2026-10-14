#!/usr/bin/env python3
"""Maintained isolated test for exact-once story-quest completion."""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path

ROM_ROOT = Path(__file__).resolve().parents[1]
if str(ROM_ROOT) not in sys.path:
    sys.path.insert(0, str(ROM_ROOT))

from data.story_quest_definitions import QuestItemDefinition, QuestType, StoryQuestDefinition
from db_modules.story_quests import activate_story_quest, add_story_quest_item, get_story_quest
from systems.story_quest_completion_system import (
    StoryQuestCompletionError,
    StoryQuestRewardError,
    complete_active_story_quest,
)


def apply_schema(db):
    path = ROM_ROOT / "migrations" / "053_story_quest_persistence_schema.py"
    spec = importlib.util.spec_from_file_location("migration_053_completion", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.up(db)


def make_quest():
    return StoryQuestDefinition(
        quest_id="fixture_item", number=1, title="fixture",
        quest_type=QuestType.QUEST_ITEM, location_id="start_path",
        unlock_level=1, previous_quest_id=None, giver_npc_id="elder",
        turn_in_npc_id="elder", description="fixture", objective_text="fixture",
        target_quantity=2,
        quest_item=QuestItemDefinition("clue", "Clue", 2, 0.5),
    )


def main():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY, gold REAL NOT NULL DEFAULT 0)")
    db.execute("""CREATE TABLE reward_ledger(
        id INTEGER PRIMARY KEY, idempotency_key TEXT NOT NULL UNIQUE,
        user_id INTEGER NOT NULL, exp INTEGER NOT NULL, gold REAL NOT NULL)""")
    apply_schema(db)
    db.execute("INSERT INTO users(user_id,gold) VALUES(1,0)")
    db.commit()
    quest = make_quest(); registry = {quest.quest_id: quest}

    activate_story_quest(
        db, user_id=1, quest_id=quest.quest_id, quest_number=1,
        target_quantity=2, timestamp="t",
    )
    db.commit()
    add_story_quest_item(
        db, user_id=1, quest_id=quest.quest_id, item_key="clue",
        quantity=1, required_quantity=2, timestamp="t",
    )
    db.commit()
    try:
        complete_active_story_quest(
            db, registry=registry, user_id=1, quest_id=quest.quest_id,
            expected_turn_in_npc_id="elder", reward_adapter=lambda **_: True,
        )
    except StoryQuestCompletionError:
        pass
    else:
        raise AssertionError("incomplete item objective was completed")

    add_story_quest_item(
        db, user_id=1, quest_id=quest.quest_id, item_key="clue",
        quantity=1, required_quantity=2, timestamp="t",
    )
    db.commit()

    def failing_reward(**kwargs):
        kwargs["connection"].execute(
            "INSERT INTO reward_ledger(idempotency_key,user_id,exp,gold) VALUES(?,?,?,?)",
            (kwargs["idempotency_key"], kwargs["user_id"], 10, 2.5),
        )
        kwargs["connection"].execute("UPDATE users SET gold=gold+2.5 WHERE user_id=1")
        raise RuntimeError("forced failure")

    try:
        complete_active_story_quest(
            db, registry=registry, user_id=1, quest_id=quest.quest_id,
            expected_turn_in_npc_id="elder", reward_adapter=failing_reward,
        )
    except StoryQuestRewardError:
        pass
    else:
        raise AssertionError("reward failure did not propagate")
    assert db.execute("SELECT COUNT(*) FROM reward_ledger").fetchone()[0] == 0
    assert db.execute("SELECT gold FROM users WHERE user_id=1").fetchone()[0] == 0
    assert db.execute("SELECT quantity FROM user_story_quest_items").fetchone()[0] == 2
    assert get_story_quest(db, 1, quest.quest_id)["status"] == "ACTIVE"

    calls = {"count": 0}
    def reward(**kwargs):
        calls["count"] += 1
        kwargs["connection"].execute(
            "INSERT INTO reward_ledger(idempotency_key,user_id,exp,gold) VALUES(?,?,?,?)",
            (kwargs["idempotency_key"], kwargs["user_id"], 10, 2.5),
        )
        kwargs["connection"].execute("UPDATE users SET gold=gold+2.5 WHERE user_id=1")
        return {"exp": 10, "gold": 2.5}

    result = complete_active_story_quest(
        db, registry=registry, user_id=1, quest_id=quest.quest_id,
        expected_turn_in_npc_id="elder", reward_adapter=reward,
    )
    assert result["completed"] and not result["already_processed"]
    replay = complete_active_story_quest(
        db, registry=registry, user_id=1, quest_id=quest.quest_id,
        expected_turn_in_npc_id="elder", reward_adapter=reward,
    )
    assert replay["already_processed"] and calls["count"] == 1
    assert db.execute("SELECT COUNT(*) FROM reward_ledger").fetchone()[0] == 1
    assert db.execute("SELECT gold FROM users WHERE user_id=1").fetchone()[0] == 2.5
    assert db.execute("SELECT COUNT(*) FROM user_story_quest_items").fetchone()[0] == 0
    row = get_story_quest(db, 1, quest.quest_id)
    assert row["status"] == "COMPLETED" and row["reward_claimed"] == 1
    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    db.close()
    print("[PASS] exact-once story quest completion")


if __name__ == "__main__":
    main()
