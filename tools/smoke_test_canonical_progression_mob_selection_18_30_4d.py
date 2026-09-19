from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];runner=R/"tools"/"run_class_progression_simulation.py";args=[sys.executable,str(runner),"--class","scout","--target-level","2","--seed","1","--max-days","30"]
a=subprocess.run(args,cwd=R,text=True,capture_output=True);b=subprocess.run(args,cwd=R,text=True,capture_output=True);assert a.returncode==b.returncode==0,(a.stderr,b.stderr)
p=R/"reports"/"simulation"/"stage_18_30_progression_scout_level_1_to_2_seed_1.json";first=json.loads(p.read_text(encoding="utf-8"));subprocess.run(args,cwd=R,text=True,capture_output=True,check=True);second=json.loads(p.read_text(encoding="utf-8"));m=second["mob_encounters"];assert m["total"]==second["battles"];assert m["unique_mobs"]>1,m;assert set(m["by_level_delta"])=={"-1","0","1"};assert m["by_level_delta"]["0"]+m["by_level_delta"]["1"]==second["battles"];assert first["mob_encounters"]==second["mob_encounters"]
assert all(abs(int(e["details"].get("level_delta",0)))<=1 for e in second["canonical_result"]["events"] if e["event_type"] in {"victory","death"});assert all(e["details"].get("candidate_count",0)>=1 for e in second["canonical_result"]["events"] if e["event_type"] in {"victory","death"})
print("[PASS] seeded canonical mob diversity, level range and deterministic replay")
