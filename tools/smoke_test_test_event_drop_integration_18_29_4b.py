# -*- coding: utf-8 -*-
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
source=(ROOT/"systems"/"reward_system.py").read_text(encoding="utf-8-sig")
tree=ast.parse(source)
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="process_victory_reward")
segment=ast.get_source_segment(source,fn) or ""
assert segment.count("ROM_STAGE_18_29_4B_EVENT_DROP_INTEGRATION")==1
assert segment.index("drop_result = process_enemy_drops(user_id, mob)") < segment.index("event_drop_results = process_event_drops(user_id, mob)")
assert '"event_drop_results": event_drop_results' in segment
from events.test_event_2026.drops import get_drop_rules
rules=get_drop_rules({"player_level":5,"location_id":"start_path"})
assert len(rules)==1
rule=rules[0]
assert rule["event_key"]=="test_event_2026" and rule["mob_key"]=="test_slime"
assert rule["item_id"]==4000 and rule["quantity"]==1 and rule["chance_percent"]==100.0
from systems.reward_system import process_event_drops
awards=[]
def fake_add(user_id,item_id,quantity):
    awards.append((user_id,item_id,quantity));return {"added":True}
event_mob={"is_event":True,"event_key":"test_event_2026","event_mob_key":"test_slime"}
result=process_event_drops(42,event_mob,random_func=lambda:0.999999,rule_collector=lambda ctx,now:rules,add_item_func=fake_add)
assert awards==[(42,4000,1)] and len(result)==1, (awards,result)
assert result[0]["payload"]["rule_id"]=="test_event_2026:test_token"
awards.clear()
normal=process_event_drops(42,{"name":"ordinary"},random_func=lambda:0.0,rule_collector=lambda ctx,now:rules,add_item_func=fake_add)
assert normal==() and awards==[]
print("TEST_EVENT_DROP_INTEGRATION_18_29_4B_OK")
