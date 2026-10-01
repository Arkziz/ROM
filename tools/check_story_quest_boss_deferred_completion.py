#!/usr/bin/env python3
from __future__ import annotations
import ast
import sqlite3
import sys
from pathlib import Path
from types import MappingProxyType
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_definitions import (
    NavigationDefinition, QuestType, RewardDefinition, StoryQuestDefinition,
)
from systems.story_quest_boss_completion_system import process_rng_boss_story_completion

source = (ROOT / "systems/story_quest_boss_completion_system.py").read_text(encoding="utf-8")
tree = ast.parse(source)
assert "complete_active_story_quest" not in source
assert "build_story_quest_reward_adapter" not in source
assert "set_story_quest_progress" in source
assert "if before >= target:" in source
assert source.count('"reason": "already_recorded"') >= 1

quest = StoryQuestDefinition(
    quest_id="fixture_story_boss", number=49, title="Fixture Boss",
    quest_type=QuestType.BOSS, location_id="start_path", unlock_level=5,
    previous_quest_id="fixture_48", giver_npc_id="mercenary_head",
    turn_in_npc_id="mercenary_head", description="Fixture boss.",
    objective_text="Defeat fixture boss.", target_quantity=1,
    boss_key="pack_leader", reward=RewardDefinition(exp=95, gold=2.15),
    navigation=NavigationDefinition(
        "start_path", "mercenary_head", "mercenary_head"
    ),
)
registry = MappingProxyType({quest.quest_id: quest})
con = sqlite3.connect(":memory:")
con.row_factory = sqlite3.Row
con.execute("""CREATE TABLE user_story_quests (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 quest_id TEXT NOT NULL,
 quest_number INTEGER NOT NULL,
 status TEXT NOT NULL,
 progress INTEGER NOT NULL,
 target_quantity INTEGER NOT NULL,
 reward_claimed INTEGER NOT NULL DEFAULT 0,
 accepted_at TEXT,
 completed_at TEXT,
 updated_at TEXT
)""")
con.execute("""INSERT INTO user_story_quests
(user_id,quest_id,quest_number,status,progress,target_quantity,reward_claimed,accepted_at,updated_at)
VALUES (1,?,49,'ACTIVE',0,1,0,'now','now')""", (quest.quest_id,))
con.commit()
mob = {"is_boss": True, "boss_key": "pack_leader"}
first = process_rng_boss_story_completion(
    user_id=1, mob=mob, location_id="start_path", encounter_id="enc-1",
    registry=registry, connection=con,
)
row = dict(con.execute("SELECT * FROM user_story_quests WHERE user_id=1").fetchone())
assert first["advanced"] is True and first["completed"] is False
assert first["reason"] == "progress_recorded"
assert row["progress"] == 1 and row["status"] == "ACTIVE"
assert row["reward_claimed"] == 0 and row["completed_at"] is None
second = process_rng_boss_story_completion(
    user_id=1, mob=mob, location_id="start_path", encounter_id="enc-1",
    registry=registry, connection=con,
)
row2 = dict(con.execute("SELECT * FROM user_story_quests WHERE user_id=1").fetchone())
assert second["advanced"] is False and second["completed"] is False
assert second["reason"] == "already_recorded"
assert row2["progress"] == row["progress"] == 1
assert row2["status"] == row["status"] == "ACTIVE"
assert row2["reward_claimed"] == row["reward_claimed"] == 0
assert row2["completed_at"] is row["completed_at"] is None
assert row2["updated_at"] == row["updated_at"]
assert row2 == row
assert process_rng_boss_story_completion(
    user_id=1, mob={"is_boss": False}, location_id="start_path",
    encounter_id="normal", registry=registry, connection=con,
)["reason"] == "not_boss"
assert process_rng_boss_story_completion(
    user_id=1, mob={"is_boss": True, "boss_key": "wrong"},
    location_id="start_path", encounter_id="wrong", registry=registry,
    connection=con,
)["reason"] == "boss_key_mismatch"
print("STORY BOSS DEFERRED COMPLETION: PASS")
