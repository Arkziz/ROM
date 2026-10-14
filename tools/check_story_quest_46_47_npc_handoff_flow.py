#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression for the canonical quest 46 to 47 NPC/item handoff."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY, STORY_QUEST_TEXT
from data.story_quest_npcs import resolve_story_quest_navigation

by_number = {quest.number: quest for quest in STORY_QUEST_REGISTRY.values()}
q46, q47 = by_number[46], by_number[47]
assert q46.quest_type.value == "QUEST_ITEM"
assert q46.giver_npc_id == "mercenary_head"
assert q46.turn_in_npc_id == "mercenary_head"
assert q46.quest_item is not None and q46.quest_item.consume_on_completion is False
assert q46.navigation.turn_in_npc_id == "mercenary_head"
assert q46.navigation.next_step_hint == resolve_story_quest_navigation("mercenary_head")["route_text"]
assert "Ковалеві" in STORY_QUEST_TEXT[q46.quest_id]["completion_text"]
assert q47.quest_type.value == "TURN_IN"
assert q47.giver_npc_id == "blacksmith" and q47.turn_in_npc_id == "blacksmith"
assert len(q47.required_quest_items) == 1
assert q47.required_quest_items[0].item_key == q46.quest_item.item_key
assert q47.required_quest_items[0].consume is True
assert q47.navigation.objective_hint == resolve_story_quest_navigation("blacksmith")["route_text"]
assert q47.navigation.next_step_hint == resolve_story_quest_navigation("blacksmith")["route_text"]
assert "Голова Найманців" in STORY_QUEST_TEXT[q47.quest_id]["acceptance_text"]
assert q47.quest_item_consumption == "atomic_exact_once"
print("STORY QUEST 46-47 NPC HANDOFF FLOW: PASS")
