from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];runner=ROOT/"tools"/"run_class_progression_simulation.py"
x=subprocess.run([sys.executable,str(runner),"--class","scout","--target-level","2","--seed","1","--max-days","30"],cwd=ROOT,text=True,capture_output=True)
assert x.returncode==0,x.stderr
assert "canonical_result" not in x.stdout and '"events"' not in x.stdout
p=ROOT/"reports"/"simulation"/"stage_18_30_progression_scout_level_1_to_2_seed_1.json";data=json.loads(p.read_text(encoding="utf-8"));assert data["target_reached"] and sum(data["encounters"].values())==data["battles"];assert data["loot_found_total"]==sum(r["found"] for r in data["loot_ledger"])
print("[PASS] compact console, encounter contract, time and loot reports")
