#!/usr/bin/env python3
"""Maintained isolated check for NPC-owned story-quest acceptance."""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_definitions import QuestType, StoryQuestDefinition
from systems.story_quest_npc_acceptance_system import (
    StoryQuestNpcAcceptanceError,
    accept_story_quest_from_npc,
    build_npc_story_quest_presentation,
)
from systems.story_quest_system import build_story_quest_registry


def apply_schema(connection):
    path = ROOT / "migrations" / "053_story_quest_persistence_schema.py"
    spec = importlib.util.spec_from_file_location("migration_053_npc_acceptance", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.up(connection)


def quest(qid, number, giver, previous=None):
    return StoryQuestDefinition(
        quest_id=qid,
        number=number,
        title=qid,
        quest_type=QuestType.TALK,
        location_id="start_path",
        unlock_level=1,
        previous_quest_id=previous,
        giver_npc_id=giver,
        turn_in_npc_id=None,
        description="fixture",
        objective_text="fixture",
        target_quantity=1,
    )


def expect_owner_error(action):
    try:
        action()
    except StoryQuestNpcAcceptanceError:
        return
    raise AssertionError("forged NPC acceptance was allowed")


def main():
    q1 = quest("q1", 1, "bartender")
    q2 = quest("q2", 2, "elder", previous="q1")
    registry = build_story_quest_registry(((q1, q2),))

    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY)")
    apply_schema(db)
    db.execute("INSERT INTO users(user_id) VALUES(1)")
    db.commit()

    bartender = build_npc_story_quest_presentation(
        db, registry=registry, user_id=1, npc_id="bartender", player_level=1
    )
    assert bartender["state"] == "AVAILABLE"
    assert bartender["actions"] == ("ACCEPT",)
    assert bartender["quest"]["quest_id"] == "q1"
    assert bartender["navigation"]["production_route_exists"]

    elder = build_npc_story_quest_presentation(
        db, registry=registry, user_id=1, npc_id="elder", player_level=1
    )
    assert elder["state"] == "NO_QUEST" and elder["actions"] == ()

    expect_owner_error(lambda: accept_story_quest_from_npc(
        db, registry=registry, user_id=1, npc_id="elder", quest_id="q1",
        player_level=1,
    ))
    result = accept_story_quest_from_npc(
        db, registry=registry, user_id=1, npc_id="bartender", quest_id="q1",
        player_level=1, timestamp="2026-01-01T00:00:00+00:00",
    )
    assert result["accepted"] and not result["already_active"]
    replay = accept_story_quest_from_npc(
        db, registry=registry, user_id=1, npc_id="bartender", quest_id="q1",
        player_level=1,
    )
    assert replay["accepted"] and replay["already_active"]
    assert db.execute(
        "SELECT COUNT(*) FROM user_story_quests WHERE user_id=1 AND status='ACTIVE'"
    ).fetchone()[0] == 1
    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    db.close()
    print("[PASS] NPC-owned story quest acceptance")


if __name__ == "__main__":
    main()
