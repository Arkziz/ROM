#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
 sys.path.insert(0,str(ROOT))
doc=json.loads((ROOT/"Квести/ROM_квести_Початок_Шляху_candidate.json").read_text(encoding="utf-8"));q={int(x["number"]):x for x in doc["quests"]};p=doc["approved_policy"]["batch_31_40_content_policy"]
assert p["section_display_title"]=="Розділ 4. Вовча загроза";assert p["kill_region_targets"]=={"32":10,"36":12,"39":12}
assert q[34]["item_reveal_policy"]["mode"]=="hide_exact_name_until_first_drop" and "Вовче хутро" not in q[34]["objective_text"]
assert q[37]["item_reveal_policy"]["mode"]=="hide_exact_name_until_first_drop" and "Рунічно позначений" not in q[37]["objective_text"]
for n,key in ((34,"start_path_runemarked_wolf_pelt"),(37,"start_path_runemarked_den_token")):assert q[n]["quest_item"]["item_key"]==key and float(q[n]["quest_item"]["drop_chance"])==0.15
for n,key in ((35,"start_path_runemarked_wolf_pelt"),(38,"start_path_runemarked_den_token")):assert q[n]["required_quest_items"]==[{"item_key":key,"quantity":1,"consume":True}] and q[n]["quest_item_consumption"]=="atomic_exact_once"
assert q[40]["quest_type"]=="TURN_IN" and not q[40].get("required_quest_items")
assert all(int(q[n]["reward"]["exp"])==48 and abs(float(q[n]["reward"]["gold"])-0.89)<1e-9 for n in range(31,41))
from data.story_quest_content import STORY_QUEST_REGISTRY
assert sorted(x.number for x in STORY_QUEST_REGISTRY.values())==list(range(1,31))
print("STORY QUEST BATCH 31-40 CONTENT POLICY: PASS")
