from __future__ import annotations
import csv,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];x=subprocess.run([sys.executable,str(R/"tools"/"run_class_progression_simulation.py"),"--class","scout","--target-level","2","--seed","1","--max-days","30"],cwd=R,text=True,capture_output=True);assert x.returncode==0,x.stderr
base=R/"reports"/"simulation";stem="stage_18_30_progression_scout_level_1_to_2_seed_1";paths=[base/(stem+".json"),base/(stem+"_loot.csv"),base/(stem+"_equipment.json")];assert all(p.is_file() for p in paths);data=json.loads(paths[0].read_text(encoding="utf-8"));equipment=json.loads(paths[2].read_text(encoding="utf-8"));rows=list(csv.DictReader(paths[1].open(encoding="utf-8-sig")))
assert data["final_loadout"],"Expected non-empty final loadout";assert equipment["final_loadout"]==data["final_loadout"];assert any(int(row["equipped"])>0 for row in rows);assert any(int(row["sold"])>0 for row in rows);assert all(row["name_uk"] and row["name_uk"]!="Спорядження 1 рівня білий" for row in rows if row["category"]=="equipment");assert all(row["found"]==row["equipped"]+row["sold"]+row["used_or_transformed"]+row["remaining"] for row in data["loot_lifecycle"]);assert "Звіти збережено (3 файли)" in x.stdout
print("[PASS] equipment lifecycle, localization, economy conservation and 3-file contract")
