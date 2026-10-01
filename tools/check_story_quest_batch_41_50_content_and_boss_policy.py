#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
path=ROOT/'Квести/ROM_квести_Початок_Шляху_candidate.json'
h=hashlib.sha256(path.read_bytes()).hexdigest();assert h=='42dabe7a630f1b5d232ed9440c654f9320735ccbcce9d74d06871b75d19966fb'
doc=json.loads(path.read_text(encoding="utf-8"));definition=lambda row:row.get("definition",row);q={int(definition(x)["number"]):x for x in doc["quests"]};p=doc["approved_policy"]["batch_41_50_content_and_boss_policy"]
assert p["section_display_title"]=="Розділ 5. Вирішальний похід"
for source,turn,key in ((43,44,"start_path_pack_leader_seal"),(46,47,"start_path_pack_leader_fur")):
 assert definition(q[source])["quest_item"]["consume_on_completion"] is False
 assert definition(q[turn])["required_quest_items"]==[{"item_key":key,"quantity":1,"consume":True}]
 assert definition(q[turn])["quest_item_consumption"]=="atomic_exact_once"
b=q[49]["boss_story_policy"]
assert b["random_hunt_encounter_allowed"] is True and b["forced_invocation_surface"]=="look_around_inline"
assert b["completion_mode"]=="deferred_turn_in_to_mercenary_head"
assert b["forced_invocation_after_victory"] is False
assert definition(q[49])["giver_npc_id"]=="mercenary_head" and (definition(q[49]).get("turn_in_npc_id") or definition(q[49])["giver_npc_id"])=="mercenary_head"
assert definition(q[50])["giver_npc_id"]=="elder" and (definition(q[50]).get("turn_in_npc_id") or definition(q[50])["giver_npc_id"])=="elder"
from data.story_quest_content import STORY_QUEST_REGISTRY
assert tuple(x.number for x in STORY_QUEST_REGISTRY.values())==tuple(range(1,41))
print("STORY QUEST BATCH 41-50 CONTENT AND BOSS POLICY: PASS")
