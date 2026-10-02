#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression for canonical navigation routes in active quests 41-50."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_npcs import resolve_story_quest_navigation

selected = sorted((q for q in STORY_QUEST_REGISTRY.values() if 41 <= q.number <= 50), key=lambda q: q.number)
assert [q.number for q in selected] == list(range(41, 51))
for quest in selected:
    assert quest.navigation is not None
    giver_route = resolve_story_quest_navigation(quest.giver_npc_id)["route_text"]
    completion_npc_id = quest.turn_in_npc_id or quest.giver_npc_id
    completion_route = resolve_story_quest_navigation(completion_npc_id)["route_text"]
    assert quest.navigation.objective_hint == giver_route, (quest.number, quest.navigation.objective_hint, giver_route)
    assert quest.navigation.next_step_hint == completion_route, (quest.number, quest.navigation.next_step_hint, completion_route)
    assert quest.objective_text not in {quest.navigation.objective_hint, quest.navigation.next_step_hint}
assert STORY_QUEST_REGISTRY[next(q.quest_id for q in selected if q.number == 41)].navigation.objective_hint == "🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста"
print("STORY QUEST BATCH 41-50 NAVIGATION ROUTES: PASS")
