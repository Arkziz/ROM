#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast,copy,hashlib,importlib,inspect,json,random,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
OUT=ROOT/"reports"/"simulation"/"stage_18_30_4c_canonical_progression_mob_selection_audit.json"
FILES=["data/mobs.py","systems/mob_system.py","systems/boss_system.py","data/bosses.py","systems/drop_system.py","systems/simulation/progression_provider.py","systems/simulation/behavior_policy.py","systems/simulation/world_progression.py","systems/simulation/loot_equipment_city.py","systems/simulation/pve_battle.py"]

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def symbol_scan(path):
 text=path.read_text(encoding="utf-8");tree=ast.parse(text);rows=[]
 for node in ast.walk(tree):
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
   rows.append({"name":node.name,"kind":"class" if isinstance(node,ast.ClassDef) else "function","line":node.lineno})
 return rows

def trace_symbols():
 wanted={
  "data.mobs":["get_mobs_for_location","get_all_mobs"],
  "systems.mob_system":["get_available_mobs","roll_is_elite","create_elite_mob"],
  "systems.boss_system":["roll_boss_encounter","build_location_boss","resolve_hunt_encounter"],
  "systems.drop_system":["roll_enemy_drops","roll_central_equipment_drop","roll_central_refine_stone_drop","roll_central_rune_drop","roll_central_potion_drop","roll_central_trophy_simple"],
  "systems.simulation.progression_provider":["ProgressionProvider"],
  "systems.simulation.behavior_policy":["BehaviorPolicy"],
  "systems.simulation.world_progression":["WorldProgressionSimulator"],
  "systems.simulation.loot_equipment_city":["LootEquipmentCityEngine"],
 }
 rows=[]
 for module_name,names in wanted.items():
  try:module=importlib.import_module(module_name)
  except Exception as e:rows.append({"module":module_name,"import_error":f"{type(e).__name__}: {e}"});continue
  for name in names:
   obj=getattr(module,name,None)
   if obj is None:continue
   try:file=Path(inspect.getsourcefile(obj) or "").resolve().relative_to(ROOT).as_posix();line=inspect.getsourcelines(obj)[1]
   except Exception:file="";line=0
   rows.append({"module":module_name,"symbol":name,"file":file,"line":line})
 return rows

def normalize(mob,location):
 return {"name":str(mob.get("name","")),"level":int(mob.get("level",1)),"min_player_level":int(mob.get("min_player_level",mob.get("level",1))),"location_id":str(mob.get("location_id",location)),"attack_type":str(mob.get("attack_type","")),"is_elite":bool(mob.get("is_elite",False)),"is_boss":bool(mob.get("is_boss",False)),"enemy_type":str(mob.get("enemy_type","normal")),"trash_items":list(mob.get("trash_items",[]) or []),"primary_stat_keys":[key for key in ("str_min","str_max","dex_min","dex_max","int_min","int_max","wis_min","wis_max","sta_min","sta_max") if key in mob]}

def main():
 before={rel:digest(ROOT/rel) for rel in FILES if (ROOT/rel).is_file()};db_before=digest(ROOT/"game.db")
 mobs_module=importlib.import_module("data.mobs");behavior_module=importlib.import_module("systems.simulation.behavior_policy");provider_module=importlib.import_module("systems.simulation.progression_provider")
 locations={key:list(value) for key,value in getattr(mobs_module,"LOCATION_MOBS_BY_LOCATION",{}).items()}
 catalog=[]
 for location,items in locations.items():catalog.extend(normalize(mob,location) for mob in items)
 by_location_level=defaultdict(list)
 for mob in catalog:by_location_level[(mob["location_id"],mob["level"])].append(mob["name"])
 counts=[{"location_id":loc,"level":lvl,"count":len(names),"names":sorted(names),"exactly_two":len(names)==2} for (loc,lvl),names in sorted(by_location_level.items())]
 production_pools=[];simulation_pools=[];selection_trials=[]
 policy=behavior_module.BehaviorPolicy()
 for location in sorted(locations):
  location_rows=[normalize(m,location) for m in mobs_module.get_mobs_for_location(location)]
  for level in sorted({1,2,3,5,10,30}|{m["level"] for m in location_rows}):
   expected=sorted([m for m in location_rows if abs(m["level"]-level)<=1],key=lambda x:(x["level"],x["name"]))
   production_pools.append({"location_id":location,"player_level":level,"rule":"location catalog + level delta -1/0/+1","count":len(expected),"mobs":[{"name":m["name"],"level":m["level"],"delta":m["level"]-level} for m in expected]})
   try:
    provider=provider_module.ProgressionProvider(ROOT,random.Random(1));actual_raw=provider.mobs(location)
   except TypeError:
    try:provider=provider_module.ProgressionProvider(ROOT,1);actual_raw=provider.mobs(location)
    except Exception as e:actual_raw=[]
   except Exception:actual_raw=[]
   actual=[normalize(m,location) for m in actual_raw if abs(int(m.get("level",1))-level)<=1]
   simulation_pools.append({"location_id":location,"player_level":level,"count":len(actual),"mobs":[{"name":m["name"],"level":m["level"],"delta":m["level"]-level} for m in sorted(actual,key=lambda x:(x["level"],x["name"]))],"missing_from_simulation":sorted(set(m["name"] for m in expected)-set(m["name"] for m in actual)),"extra_in_simulation":sorted(set(m["name"] for m in actual)-set(m["name"] for m in expected))})
   if expected:
    picks=[]
    for seed in range(1,101):
     selected=policy.select_mob(level,[copy.deepcopy(m) for m in expected],"")
     if selected:picks.append(str(selected.get("name","")))
    selection_trials.append({"location_id":location,"player_level":level,"candidate_count":len(expected),"trials":100,"selected_counts":dict(sorted(Counter(picks).items())),"unique_selected":len(set(picks)),"deterministic_first_candidate_bias":len(set(picks))==1 and len(expected)>1})
 source_symbols={rel:symbol_scan(ROOT/rel) for rel in FILES if (ROOT/rel).is_file()}
 findings=[]
 if any(row["deterministic_first_candidate_bias"] for row in selection_trials):findings.append({"severity":"BLOCKING","code":"SIM_SELECTION_NOT_RANDOM","message":"BehaviorPolicy.select_mob deterministically chooses one preferred mob from a multi-mob pool; seeded RNG is not used."})
 if any(row["count"]!=2 for row in counts):findings.append({"severity":"INFO","code":"CATALOG_COUNT_NOT_ALWAYS_TWO","message":"At least one location-level bucket does not contain exactly two configured normal mobs; inspect catalog details before enforcing a count."})
 mismatches=[row for row in simulation_pools if row["missing_from_simulation"] or row["extra_in_simulation"]]
 if mismatches:findings.append({"severity":"BLOCKING","code":"PRODUCTION_SIMULATION_POOL_MISMATCH","message":"Simulation and canonical location/level pools differ for one or more probes.","probe_count":len(mismatches)})
 findings.append({"severity":"REQUIRED","code":"HUMAN_PLAY_PARITY_SCOPE","message":"Restoration must reuse canonical mob/location, encounter, battle, drop, inventory, equipment, rune, potion, repair, fatigue, city and time-window paths; no synthetic mob or loot catalog may be introduced."})
 report={"stage":"18.30.4c","status":"PASS","audit_mode":"read_only","database_mutation":False,"catalog":{"mob_count":len(catalog),"locations":sorted(locations),"mobs":catalog,"counts_by_location_and_level":counts},"production_path":{"symbols":trace_symbols(),"ordered_flow":["hunt input","activity window and fatigue gate","current location","canonical location mob catalog","player level delta -1/0/+1 filter","random normal candidate selection","elite roll / modifier","boss encounter roll / canonical boss builder","canonical PvE actor and battle","canonical central drop rolls","inventory capacity","equipment comparison and equip/sale","runes, potions, refine, repair and city maintenance","EXP/gold/time/event reporting"]},"production_pool_probes":production_pools,"simulation_pool_probes":simulation_pools,"selection_trials":selection_trials,"source_symbols":source_symbols,"findings":findings,"recommended_restore_contract":{"existing_mobs_only":True,"existing_loot_only":True,"location_aware":True,"level_delta_allowed":[-1,0,1],"seeded_random_selection":True,"elite_after_normal_selection":True,"boss_separate_from_normal_pool":True,"report_encounters_by_name_level_delta_type":True,"maximum_transferable_reports":3},"integrity":{"game_db_sha256_before":db_before,"game_db_sha256_after":digest(ROOT/"game.db"),"source_sha256_before":before,"source_sha256_after":{rel:digest(ROOT/rel) for rel in before}}}
 report["integrity"]["unchanged"]=report["integrity"]["game_db_sha256_before"]==report["integrity"]["game_db_sha256_after"] and report["integrity"]["source_sha256_before"]==report["integrity"]["source_sha256_after"]
 if not report["integrity"]["unchanged"]:raise RuntimeError("Read-only integrity violation")
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+chr(10),encoding="utf-8")
 print("[PASS] Read-only canonical mob selection and human-play parity audit")
 print(f"[INFO] Canonical mobs: {len(catalog)}; locations: {len(locations)}; findings: {len(findings)}")
 print(f"[REPORT] {OUT.relative_to(ROOT)}")
 return 0
if __name__=="__main__":raise SystemExit(main())
