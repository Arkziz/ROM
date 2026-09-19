from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];x=subprocess.run([sys.executable,str(R/"tools"/"run_class_progression_simulation.py"),"--class","scout","--target-level","2","--seed","1","--max-days","30"],cwd=R,text=True,capture_output=True);assert x.returncode==0,x.stderr
base=R/"reports"/"simulation";stem="stage_18_30_progression_scout_level_1_to_2_seed_1";data=json.loads((base/(stem+".json")).read_text(encoding="utf-8"));eq=json.loads((base/(stem+"_equipment.json")).read_text(encoding="utf-8"));assert len(list(base.glob(stem+"*")))==3
armor=[i for i in eq["final_loadout"] if i["slot_key"] in {"helmet","shoulders","legs"}];assert armor and all(i["armor_type"]=="leather" for i in armor);assert all("[Шкіра]" in i["name_uk"] for i in armor);weapon=next(i for i in eq["final_loadout"] if i["slot_key"]=="main_hand");assert weapon["name_uk"].startswith("⚪ Лук ");assert all((f"+{i['refine_level']}" in i["name_uk"]) if i["refine_level"] else "+" not in i["name_uk"] for i in eq["final_loadout"]);assert eq["final_loadout"]==data["final_loadout"]
print("[PASS] equipment metadata and canonical Ukrainian display format")
