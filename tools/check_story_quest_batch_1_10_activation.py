#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
from data.story_quest_definitions import QuestType
assert len(STORY_QUEST_REGISTRY)==10
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values())==tuple(range(1,11))
assert 'start_path_011_unstable_glow' not in STORY_QUEST_REGISTRY
assert [q.target_quantity for q in STORY_QUEST_REGISTRY.values() if q.quest_type is QuestType.KILL_REGION]==[3,5,6]
assert all(abs(q.reward.gold-0.27)<1e-9 and q.reward.exp==30 for q in STORY_QUEST_REGISTRY.values())
assert STORY_QUEST_REGISTRY['start_path_004_guard_uniform_scrap'].quest_item.consume_on_completion is False
assert STORY_QUEST_REGISTRY['start_path_007_broken_guard_lantern'].quest_item.consume_on_completion is False
assert len(STORY_QUEST_TEXT)==10
from handlers.story_quest_npc_runtime import register_story_quest_npc_runtime_handlers,send_story_npc_if_present
print('STORY QUEST BATCH 1-10 ACTIVATION: PASS')
