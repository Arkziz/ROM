#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import events
from systems.boss_system import generate_hunt_encounter

class Rng:
    def __init__(self,values): self.values=iter(values)
    def random(self): return next(self.values)

def factory(template=None):
    source=template or {"name":"normal"}
    return {"name":source["name"],"hp":10,"max_hp":10,"attack":2,"pdef":1,"mdef":1,"dex":1,"wis":1,"attack_type":"physical"}

def elite(mob): mob["is_elite"]=True; return mob
def never_elite(): return False
empty=lambda context,now: ()
normal=generate_hunt_encounter(5,"start_path",factory,elite,never_elite,rng=Rng([0.99]),boss_enabled=False,event_candidate_collector=empty)
assert normal["enemy_type"]=="normal" and normal["mob"]["name"]=="normal"
assert events.select_event_mob_candidate((),rng=Rng([0.0]),chance_percent=100) is None
candidate={"event_key":"pilot","mob_key":"mob","weight":1,"chance_percent":100,"mob_template":{"name":"event"}}
selected=generate_hunt_encounter(5,"start_path",factory,elite,never_elite,rng=Rng([0.0,0.0]),boss_enabled=False,event_candidate_collector=lambda context,now:(candidate,))
assert selected["enemy_type"]=="event_normal"
assert selected["mob"]["name"]=="event" and selected["mob"]["is_event"] is True
assert selected["mob"]["event_key"]=="pilot" and selected["mob"]["event_mob_key"]=="mob"
miss=generate_hunt_encounter(5,"start_path",factory,elite,never_elite,rng=Rng([0.99]),boss_enabled=False,event_chance_percent=0,event_candidate_collector=lambda context,now:(candidate,))
assert miss["enemy_type"]=="normal"
weighted=events.select_event_mob_candidate((candidate,{**candidate,"mob_key":"second","weight":3}),rng=Rng([0.0,0.9]),chance_percent=100)
assert weighted["mob_key"]=="second"
try: events.validate_event_mob_candidates(({**candidate,"weight":0},))
except events.EventRegistryError as exc: assert "positive" in str(exc)
else: raise AssertionError("zero weight accepted")
print("NORMAL_EVENT_ENCOUNTERS_18_28_6_OK")
