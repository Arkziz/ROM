#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
from data.story_quest_hierarchy import validate_story_hierarchy_metadata,get_story_section
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values())==tuple(range(1,81))
s=get_story_section("dark_forest_03");assert s.quest_numbers==tuple(range(71,81)) and s.required_level==8
m=validate_story_hierarchy_metadata();assert m["production_quest_count"]==80 and m["metadata_quest_count"]==80
q71=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==71);text=STORY_QUEST_TEXT[q71.quest_id]["acceptance_text"]+"\n"+STORY_QUEST_TEXT[q71.quest_id]["completion_text"]
for p in ("Відтисни гоблінські загони","відкрий прохід для розвідників","Не заходь за кам’яний прохід"):assert p.casefold() not in text.casefold()
q74=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==74);q78=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==78);assert q74.quest_item.drop_chance==q78.quest_item.drop_chance==0.15
q75=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==75);q79=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==79);q80=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==80);assert q75.required_quest_items[0].consume and q79.required_quest_items[0].consume and not q80.required_quest_items
print("PASS: Stage 19.31.3")
