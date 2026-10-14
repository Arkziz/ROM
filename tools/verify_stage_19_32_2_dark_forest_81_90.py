#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_hierarchy import validate_story_hierarchy_metadata,get_story_section
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values())==tuple(range(1,91))
s=get_story_section("dark_forest_04");assert s.quest_numbers==tuple(range(81,91)) and s.required_level==9
m=validate_story_hierarchy_metadata();assert m["production_quest_count"]==90 and m["metadata_quest_count"]==90
q84=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==84);q88=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==88);assert q84.quest_item.drop_chance==q88.quest_item.drop_chance==0.15 and not q84.quest_item.consume_on_completion and not q88.quest_item.consume_on_completion
q85=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==85);q89=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==89);q90=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==90);assert q85.required_quest_items[0].consume and q89.required_quest_items[0].consume and not q90.required_quest_items
print("PASS: Stage 19.32.2")
