#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_definitions import QuestType
from data.story_quest_hierarchy import validate_story_hierarchy_metadata,get_story_section
from data.bosses import get_boss_definition
from systems.story_quest_boss_call_system import get_active_story_boss_call
from systems.story_quest_boss_completion_system import process_rng_boss_story_completion
from systems.story_boss_invocation_adapter import build_story_boss_look_around_presentation
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values())==tuple(range(1,101))
s=get_story_section("dark_forest_05");assert s.quest_numbers==tuple(range(91,101)) and s.required_level==10
m=validate_story_hierarchy_metadata();assert m["production_quest_count"]==100 and m["metadata_quest_count"]==100
q99=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==99);assert q99.quest_type is QuestType.BOSS and q99.boss_key=="goblin_king" and q99.location_id=="dark_forest" and q99.target_quantity==1
b=get_boss_definition("goblin_king");assert b and b["location_id"]=="dark_forest" and b["level_max"]>=10
q94=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==94);q95=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==95);q100=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==100);assert q94.quest_item.drop_chance==0.15 and not q94.quest_item.consume_on_completion and q95.required_quest_items[0].consume and not q100.required_quest_items
print("PASS: Stage 19.33.3")
