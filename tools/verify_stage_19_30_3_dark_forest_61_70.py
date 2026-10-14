#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
from data.story_quest_hierarchy import validate_story_hierarchy_metadata,get_story_section
nums=tuple(q.number for q in STORY_QUEST_REGISTRY.values())
assert nums==tuple(range(1,71))
section=get_story_section("dark_forest_02")
assert section.quest_numbers==tuple(range(61,71)) and section.required_level==7
meta=validate_story_hierarchy_metadata()
assert meta["production_quest_count"]==70 and meta["metadata_quest_count"]==70
q61=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==61)
merged=STORY_QUEST_TEXT[q61.quest_id]["acceptance_text"]+"\n"+STORY_QUEST_TEXT[q61.quest_id]["completion_text"]
for phrase in ("Перший удар потрібно завдати","під час зміни варти","Я покажу місце"):assert phrase.casefold() not in merged.casefold()
q64=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==64);q68=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==68)
assert q64.quest_item.drop_chance==q68.quest_item.drop_chance==0.15
q69=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==69);q70=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==70)
assert q69.required_quest_items[0].consume is False and q70.required_quest_items[0].consume is True
print("PASS: Stage 19.30.3")
