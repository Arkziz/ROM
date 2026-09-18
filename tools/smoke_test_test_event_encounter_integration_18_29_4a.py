# -*- coding: utf-8 -*-
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from systems.combat_system import generate_hunt_encounter
from events.test_event_2026.mobs import get_mob_candidates
class HitRng:
    @staticmethod
    def random(): return 0.0
class MissRng:
    @staticmethod
    def random(): return 0.999999

def normal_factory(template=None):
    source=dict(template or {"name":"Звичайний","attack_type":"physical","level":5})
    source.setdefault("name","Звичайний");source.setdefault("attack_type","physical");source["level"]=5
    source.update({"hp":50,"max_hp":50,"attack":10,"pdef":2,"mdef":2,"def":2,"str":5,"dex":5,"int":1,"wis":1,"sta":5})
    return source
context={"player_level":5,"location_id":"start_path"}
candidates=get_mob_candidates(context)
assert len(candidates)==1 and candidates[0]["chance_percent"]==25.0
hit=generate_hunt_encounter(5,"start_path",normal_factory,lambda m:m,lambda:False,rng=HitRng(),boss_enabled=False,event_enabled=True,event_chance_percent=25.0,event_context=context,event_candidate_collector=lambda ctx,now:candidates)
mob=hit["mob"]
assert hit["enemy_type"]=="event_normal"
assert mob["name"]=="🧪 Нестабільний слизень"
assert mob["event_key"]=="test_event_2026" and mob["event_mob_key"]=="test_slime"
assert mob["is_event"] is True and mob["is_elite"] is False and mob["is_boss"] is False
assert mob["level"]==5 and mob["attack_type"]=="physical"
miss=generate_hunt_encounter(5,"start_path",normal_factory,lambda m:m,lambda:False,rng=MissRng(),boss_enabled=False,event_enabled=True,event_chance_percent=25.0,event_context=context,event_candidate_collector=lambda ctx,now:candidates)
assert miss["enemy_type"]=="normal" and not miss["mob"].get("is_event")
disabled=generate_hunt_encounter(5,"start_path",normal_factory,lambda m:m,lambda:False,rng=HitRng(),boss_enabled=False,event_enabled=False,event_chance_percent=25.0,event_context=context,event_candidate_collector=lambda ctx,now:(_ for _ in ()).throw(AssertionError("collector called while disabled")))
assert disabled["enemy_type"]=="normal"
assert get_mob_candidates({"player_level":0,"location_id":"start_path"})==()
assert get_mob_candidates({"player_level":31,"location_id":"start_path"})==()
print("TEST_EVENT_ENCOUNTER_INTEGRATION_18_29_4A_OK")
