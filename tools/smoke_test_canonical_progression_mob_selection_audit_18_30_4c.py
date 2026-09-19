from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];tool=R/"tools"/"audit_canonical_progression_mob_selection.py";out=R/"reports"/"simulation"/"stage_18_30_4c_canonical_progression_mob_selection_audit.json"
x=subprocess.run([sys.executable,str(tool)],cwd=R,text=True,capture_output=True);assert x.returncode==0,x.stderr;data=json.loads(out.read_text(encoding="utf-8"));assert data["audit_mode"]=="read_only" and data["integrity"]["unchanged"];assert data["catalog"]["mob_count"]>0;assert data["production_path"]["symbols"];assert data["production_pool_probes"] and data["simulation_pool_probes"] and data["selection_trials"];assert data["recommended_restore_contract"]["existing_mobs_only"];assert data["recommended_restore_contract"]["existing_loot_only"];print("[PASS] canonical progression mob selection audit contract")
