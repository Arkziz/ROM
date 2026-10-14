#!/usr/bin/env python3
"""Maintained isolated integration check for the story-quest lifecycle engine."""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path

ROM_ROOT = Path(__file__).resolve().parents[1]
if str(ROM_ROOT) not in sys.path:
    sys.path.insert(0, str(ROM_ROOT))

from data.story_quest_definitions import (
    NavigationDefinition,
    QuestItemDefinition,
    QuestType,
    StoryQuestDefinition,
)
from systems.story_quest_system import (
    StoryQuestUnavailableError,
    accept_story_quest,
    advance_region_kill_progress,
    build_story_quest_registry,
    collect_active_quest_item,
    get_story_quest_status,
    get_story_quest_view,
    skip_overlevel_active_quest,
)


def apply_schema(connection):
    path = ROM_ROOT / "migrations" / "053_story_quest_persistence_schema.py"
    spec = importlib.util.spec_from_file_location("migration_053_lifecycle", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.up(connection)


def quest(qid, number, qtype, previous=None, **updates):
    values = dict(
        quest_id=qid, number=number, title=qid, quest_type=qtype,
        location_id="start_path", unlock_level=1, previous_quest_id=previous,
        giver_npc_id="elder", turn_in_npc_id=None,
        description="fixture", objective_text="fixture", target_quantity=1,
        navigation=NavigationDefinition("start_path", "elder"),
    )
    values.update(updates)
    return StoryQuestDefinition(**values)


def expect_unavailable(action):
    try:
        action()
    except StoryQuestUnavailableError:
        return
    raise AssertionError("locked quest was accepted")


def main():
    talk = quest("q1", 1, QuestType.TALK)
    kill = quest("q2", 2, QuestType.KILL_REGION, "q1", target_quantity=2)
    item = quest(
        "q3", 3, QuestType.QUEST_ITEM, "q2", target_quantity=2,
        turn_in_npc_id="elder",
        quest_item=QuestItemDefinition("wolf_clue", "Wolf Clue", 2, 0.5),
        navigation=NavigationDefinition("start_path", "elder", "elder"),
    )
    registry = build_story_quest_registry(((talk, kill, item),))

    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY)")
    apply_schema(db)
    db.execute("INSERT INTO users(user_id) VALUES(1)")
    db.commit()

    assert get_story_quest_status(
        db, user_id=1, quest=talk, player_level=1
    ).value == "AVAILABLE"
    assert get_story_quest_status(
        db, user_id=1, quest=kill, player_level=1
    ).value == "LOCKED"

    accepted = accept_story_quest(
        db, registry=registry, user_id=1, quest_id="q1", player_level=1,
        timestamp="2026-01-01T00:00:00+00:00",
    )
    assert accepted["status"] == "ACTIVE"
    assert accept_story_quest(
        db, registry=registry, user_id=1, quest_id="q1", player_level=1,
    )["id"] == accepted["id"]
    expect_unavailable(lambda: accept_story_quest(
        db, registry=registry, user_id=1, quest_id="q2", player_level=1,
    ))

    # The completion service is a later stage. Seed finalized predecessor rows
    # directly only inside this isolated checker to exercise subsequent states.
    db.execute("UPDATE user_story_quests SET status='COMPLETED', reward_claimed=1 WHERE quest_id='q1'")
    db.commit()
    accept_story_quest(db, registry=registry, user_id=1, quest_id="q2", player_level=1)
    assert advance_region_kill_progress(
        db, registry=registry, user_id=1, location_id="dark_forest"
    )["reason"] == "location_mismatch"
    assert advance_region_kill_progress(
        db, registry=registry, user_id=1, location_id="start_path"
    )["progress"] == 1
    final_kill = advance_region_kill_progress(
        db, registry=registry, user_id=1, location_id="start_path", amount=5
    )
    assert final_kill["progress"] == 2 and final_kill["objective_complete"]

    db.execute("UPDATE user_story_quests SET status='COMPLETED', reward_claimed=1 WHERE quest_id='q2'")
    db.commit()
    accept_story_quest(db, registry=registry, user_id=1, quest_id="q3", player_level=1)
    assert collect_active_quest_item(
        db, registry=registry, user_id=1, location_id="start_path",
        item_key="wrong",
    )["reason"] == "item_key_mismatch"
    collected = collect_active_quest_item(
        db, registry=registry, user_id=1, location_id="start_path",
        item_key="wolf_clue", amount=5,
    )
    assert collected["quantity"] == 2 and collected["objective_complete"]
    view = get_story_quest_view(db, user_id=1, quest=item, player_level=1)
    assert view["status"] == "ACTIVE" and view["quest_item_quantity"] == 2

    assert skip_overlevel_active_quest(
        db, registry=registry, user_id=1, current_level=5,
        location_max_levels={"start_path": 5},
    ) is None
    skipped = skip_overlevel_active_quest(
        db, registry=registry, user_id=1, current_level=6,
        location_max_levels={"start_path": 5},
    )
    assert skipped["status"] == "SKIPPED" and skipped["reward_claimed"] == 0
    assert db.execute("SELECT COUNT(*) FROM user_story_quest_items").fetchone()[0] == 0
    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    db.close()
    print("[PASS] story quest lifecycle engine")


if __name__ == "__main__":
    main()
