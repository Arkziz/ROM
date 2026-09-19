from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];x=subprocess.run([sys.executable,str(R/"tools"/"run_class_progression_simulation.py"),"--class","scout","--target-level","2","--seed","1","--max-days","30"],cwd=R,text=True,capture_output=True);assert x.returncode==0,x.stderr;assert "canonical_result" not in x.stdout
p=R/"reports"/"simulation"/"stage_18_30_progression_scout_level_1_to_2_seed_1.json";d=json.loads(p.read_text(encoding="utf-8"));assert d["loot_lifecycle"] and all(row["name_uk"] for row in d["loot_lifecycle"]);assert all(row["found"]==row["equipped"]+row["sold"]+row["used_or_transformed"]+row["remaining"] for row in d["loot_lifecycle"]);assert "from_mobs" in d["economy"];print("[PASS] localized economy, equipment and loot lifecycle reporting")
