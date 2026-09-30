#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
doc=json.loads((ROOT/"Квести/ROM_квести_Початок_Шляху_candidate.json").read_text(encoding="utf-8"))
batch=sorted((q for q in doc["quests"] if 31<=int(q["number"])<=40),key=lambda q:int(q["number"]))
assert [int(q["number"]) for q in batch]==list(range(31,41))
by={int(q["number"]):q for q in doc["quests"]}
for q in batch:
 n=int(q["number"]);assert q["previous_quest_id"]==by[n-1]["quest_id"];assert int(q["unlock_level"])==4;assert q["location_id"]=="start_path"
 r=q["reward"];f=r["formula"];assert int(r["exp"])==48;assert abs(float(r["gold"])-0.89)<1e-9;assert f["reference_enemy_type"]=="normal";assert int(f["reference_enemy_level"])==4;assert int(f["multiplier"])==3
 text=json.dumps(q,ensure_ascii=False).casefold();assert not any(term in text for term in ("глава","главу","глави"))
from data.story_quest_content import STORY_QUEST_REGISTRY
assert sorted(q.number for q in STORY_QUEST_REGISTRY.values())==list(range(1,31))
assert not any(31<=q.number<=40 for q in STORY_QUEST_REGISTRY.values())
from data.story_quest_npcs import resolve_story_quest_navigation
for npc_id in sorted({q[k] for q in batch for k in ("giver_npc_id","turn_in_npc_id")}):
 route=resolve_story_quest_navigation(npc_id);assert route and route.get("route_text")
print("STORY QUEST BATCH 31-40 AUDIT: PASS")
