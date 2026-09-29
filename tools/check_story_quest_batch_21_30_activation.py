#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quests.start_path_21_30 import QUEST_ROWS
nums=sorted(q.number for q in STORY_QUEST_REGISTRY.values());assert nums==list(range(1,31)) and 31 not in nums
assert all(isinstance(x,dict) and isinstance(x.get("definition"),dict) for x in QUEST_ROWS)
assert [x["definition"]["number"] for x in QUEST_ROWS]==list(range(21,31))
assert all(set(x["definition"]["reward"])=={"exp","gold"} for x in QUEST_ROWS)
assert all("drop_message" not in (x["definition"].get("quest_item") or {}) for x in QUEST_ROWS)
by={q.number:q for q in STORY_QUEST_REGISTRY.values()};assert all(q.unlock_level==3 and q.reward.exp==42 and abs(q.reward.gold-.65)<1e-12 for n,q in by.items() if 21<=n<=30)
assert by[24].quest_type.value=="TALK" and by[30].quest_type.value=="TURN_IN" and len(by[30].required_quest_items)==3
print("STORY QUESTS 21-30 ACTIVATION: PASS")
