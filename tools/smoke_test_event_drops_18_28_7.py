#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import events
from events import item_namespace as ns
from systems.drop_system import get_event_drop_plan
from systems.reward_system import process_event_drops
ns.EVENT_ITEM_BLOCKS.update({"pilot":(4000,4049)})
mob={"is_event":True,"event_key":"pilot","event_mob_key":"wolf"}
rule={"rule_id":"pilot:currency","event_key":"pilot","mob_key":"wolf","item_id":4000,"quantity":2,"chance_percent":100}
assert get_event_drop_plan({},rule_collector=lambda c,n:(rule,))==()
plan=get_event_drop_plan(mob,random_func=lambda:0.0,rule_collector=lambda c,n:(rule,))
assert plan==({"rule_id":"pilot:currency","event_key":"pilot","item_id":4000,"quantity":2},)
assert get_event_drop_plan(mob,random_func=lambda:0.99,rule_collector=lambda c,n:({**rule,"chance_percent":0},))==()
added=[]
result=process_event_drops(7,mob,random_func=lambda:0.0,rule_collector=lambda c,n:(rule,),add_item_func=lambda uid,iid,qty: added.append((uid,iid,qty)) or {"added":qty})
assert added==[(7,4000,2)] and result[0]["result"]["added"]==2
try: events.validate_event_drop_rules(({**rule,"item_id":4050},),mob)
except Exception as exc: assert "outside block" in str(exc)
else: raise AssertionError("foreign block accepted")
try: events.validate_event_drop_rules((rule,dict(rule)),mob)
except events.EventRegistryError as exc: assert "unique" in str(exc)
else: raise AssertionError("duplicate rule accepted")
ns.EVENT_ITEM_BLOCKS.clear()
print("EVENT_DROPS_18_28_7_OK")
