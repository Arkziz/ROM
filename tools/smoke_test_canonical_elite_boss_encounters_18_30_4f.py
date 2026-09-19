from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from systems.simulation.progression_provider import ProgressionProvider
from systems.simulation.rng import SimulationRng
p=ProgressionProvider();templates=p.mobs(1);assert templates
def sequence(seed,n=600):
 rng=SimulationRng(seed);rows=[]
 for i in range(n):
  template=rng.choice(templates);mob=p.resolve_encounter(1,template,rng);rows.append((mob["enemy_type"],mob["name"],mob["level"],bool(mob.get("is_elite")),bool(mob.get("is_boss"))))
 return rows
a=sequence(11);b=sequence(11);assert a==b;types={row[0] for row in a};assert {"normal","elite","boss"}.issubset(types),types
assert all(row[2]==1 for row in a if row[0]=="boss");assert all(row[3] and not row[4] for row in a if row[0]=="elite");assert all(row[4] and not row[3] for row in a if row[0]=="boss")
runner=R/"tools"/"run_class_progression_simulation.py";x=subprocess.run([sys.executable,str(runner),"--class","scout","--target-level","2","--seed","2","--max-days","30"],cwd=R,text=True,capture_output=True);assert x.returncode==0,x.stderr
data=json.loads((R/"reports"/"simulation"/"stage_18_30_progression_scout_level_1_to_2_seed_2.json").read_text(encoding="utf-8"));assert sum(data["encounters"].values())==data["battles"];assert data["mob_encounters"]["total"]==data["battles"]
print("[PASS] canonical normal, elite and boss encounter adapter with deterministic replay")
