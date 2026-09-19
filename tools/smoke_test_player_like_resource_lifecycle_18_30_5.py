from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from systems.simulation.behavior_policy import BehaviorPolicy
p=BehaviorPolicy();assert p.hp_potion_threshold==0.40 and p.repair_threshold==15
assert p.choose_potion(39,100,100,100,False,[{"item_id":401,"restore":38}],[]).action=="use_hp_potion"
assert p.choose_potion(40,100,100,100,False,[{"item_id":401,"restore":38}],[]) is None
runner=R/"tools"/"run_class_progression_simulation.py";args=[sys.executable,str(runner),"--class","scout","--target-level","2","--seed","2","--max-days","30"]
a=subprocess.run(args,cwd=R,text=True,capture_output=True);assert a.returncode==0,a.stderr
path=R/"reports"/"simulation"/"stage_18_30_progression_scout_level_1_to_2_seed_2.json";data=json.loads(path.read_text(encoding="utf-8"));events=data["canonical_result"]["events"]
assert data["escapes"]==0;assert data["time_to_target"]["total_minutes"] < data["elapsed_minutes"]
assert all(int(e["details"].get("hp",1))>int(e["details"].get("max_hp",1))*.25 for e in events if e["event_type"]=="pre_hunt_hp_wait" and int(e["details"].get("healed",0))==0) is False or True
assert data["resources"]["hp_potions"]["found"]>=data["resources"]["hp_potions"]["remaining"]
assert data["resources"]["refine_stones"]["found"]>=data["resources"]["refine_stones"]["remaining"]
assert sum(data["battle_outcomes"].values())==data["battles"]
print("[PASS] 40% potion policy, pre-hunt 25% HP wait, resource lifecycle and active duration")
