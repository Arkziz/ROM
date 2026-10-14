#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression for content quality and immutable gameplay in quests 41-50."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_content import STORY_QUEST_REGISTRY, STORY_QUEST_TEXT
from data.story_quest_npcs import resolve_story_quest_navigation

def norm(value):
    return re.sub(r"\s+", " ", str(value)).strip().casefold()

def words(value):
    return len(re.findall(r"[\w’'-]+", str(value), flags=re.UNICODE))

selected = sorted((q for q in STORY_QUEST_REGISTRY.values() if 41 <= q.number <= 50), key=lambda q: q.number)
assert [q.number for q in selected] == list(range(41, 51))
for quest in selected:
    texts = STORY_QUEST_TEXT[quest.quest_id]
    values = [quest.description, texts["acceptance_text"], texts["progress_text"], texts["completion_text"]]
    assert len({norm(value) for value in values}) == 4, quest.number
    assert words(quest.description) >= 10, (quest.number, "description")
    assert words(texts["acceptance_text"]) >= 20, (quest.number, "acceptance_text")
    assert words(texts["progress_text"]) >= 10, (quest.number, "progress_text")
    assert words(texts["completion_text"]) >= 14, (quest.number, "completion_text")
    assert quest.navigation.objective_hint == resolve_story_quest_navigation(quest.giver_npc_id)["route_text"]
    completion_npc = quest.turn_in_npc_id or quest.giver_npc_id
    assert quest.navigation.next_step_hint == resolve_story_quest_navigation(completion_npc)["route_text"]
    assert norm(quest.objective_text) not in {norm(value) for value in values}
assert [q.quest_type.value for q in selected] == ["TALK","KILL_REGION","QUEST_ITEM","TURN_IN","KILL_REGION","QUEST_ITEM","TURN_IN","KILL_REGION","BOSS","TURN_IN"]
assert [q.target_quantity for q in selected if q.number in (42,45,48)] == [15,15,10]
assert all(q.quest_item.drop_chance == 0.15 for q in selected if q.number in (43,46))
assert next(q for q in selected if q.number == 49).boss_key == "pack_leader"
assert not next(q for q in selected if q.number == 50).required_quest_items
print("STORY QUEST BATCH 41-50 CONTENT QUALITY: PASS")
