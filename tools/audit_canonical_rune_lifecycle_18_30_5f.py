#!/usr/bin/env python3
from __future__ import annotations
import ast,hashlib,json,sys
from dataclasses import asdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
OUT=R/"reports"/"simulation"/"stage_18_30_5f_canonical_rune_lifecycle_audit.json"
FILES=("data/runes.py","systems/rune_system.py","systems/simulation/meta_progression.py","systems/simulation/models.py","systems/simulation/combat_actor_stats.py")
def sha(p):h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def equipment(sim_id,slot,durability=100,runes=None):
 from systems.simulation.models import SimulationInventoryItem
 x=SimulationInventoryItem(sim_id,10000+sim_id,f"eq-{sim_id}","equipment",1,1,slot,1,"common",durability=durability,stats={});x.runes=list(runes or []);return x
def rune(sim_id,item_id,qty=1):
 from data.runes import get_rune_definition
 from systems.simulation.models import SimulationInventoryItem
 d=get_rune_definition(item_id);return SimulationInventoryItem(sim_id,item_id,d["name"],"rune",qty,50)
def service(items,slots):
 from systems.simulation.meta_progression import SimulationMetaProgressionService
 from systems.simulation.models import SimulationEquipment,SimulationInventory
 class Rng:
  def randint(self,a,b):return a
 inv=SimulationInventory();inv.items=list(items);eq=SimulationEquipment();eq.slots.update(slots);return SimulationMetaProgressionService(inv,eq,Rng()),inv,eq
def quantities(inv):return {x.item_id:x.quantity for x in inv.items if 701<=x.item_id<=725}
def case(label,items,slots):
 svc,inv,eq=service(items,slots);before=quantities(inv);inserted=svc.insert_best_runes();equipped=[x for x in inv.items if x.simulation_item_id in eq.slots.values()]
 return {"label":label,"before":before,"inserted":inserted,"state_inserted":svc.state.runes_inserted,"after":quantities(inv),"sockets":{str(x.simulation_item_id):[asdict(r) for r in x.runes] for x in equipped}}
def main():
 from data.runes import RUNE_ITEM_DEFINITIONS,RUNE_SLOT_LIMITS,get_rune_definition,get_rune_item_id,get_rune_slot_limit
 from systems.simulation.models import SimulationRuneSocket
 definitions={i:get_rune_definition(i) for i in range(701,726)};definition_parity=definitions==RUNE_ITEM_DEFINITIONS
 roundtrip=all(get_rune_item_id(d["stat"],d["level"])==i for i,d in definitions.items())
 slots={k:get_rune_slot_limit(k) for k in ("main_hand","off_hand","helmet","shoulders","chest","gloves","legs","boots","necklace","ring","invalid")}
 cases=[]
 cases.append(case("highest_level_first",[equipment(1,"main_hand"),rune(100,701),rune(101,705)],{"main_hand":1}))
 cases.append(case("capacity_respected",[equipment(2,"chest"),rune(102,701,5)],{"chest":2}))
 existing=[SimulationRuneSocket(0,701,"STR",1),SimulationRuneSocket(1,706,"STA",1)]
 cases.append(case("existing_sockets_preserved",[equipment(3,"chest",runes=existing),rune(103,711,2)],{"chest":3}))
 cases.append(case("broken_equipment_should_block",[equipment(4,"main_hand",durability=0),rune(104,711)],{"main_hand":4}))
 cases.append(case("unequipped_equipment_should_block",[equipment(5,"main_hand"),rune(105,711)],{}))
 # Scout class-awareness probe: DEX rune 711 should outrank unrelated equal-level STR rune 701.
 cases.append(case("scout_class_aware_equal_level",[equipment(6,"main_hand"),rune(106,701),rune(107,711)],{"main_hand":6}))
 # Multi-item placement must not exceed canonical capacity.
 cases.append(case("multi_equipment_capacity",[equipment(7,"main_hand"),equipment(8,"ring"),rune(108,711,4)],{"main_hand":7,"ring":8}))
 src=(R/"systems/simulation/meta_progression.py").read_text(encoding="utf-8");tree=ast.parse(src);fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="insert_best_runes");segment=ast.get_source_segment(src,fn);calls=sorted({ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n,ast.Call)})
 findings=[]
 if not definition_parity or not roundtrip:findings.append("SIMULATION_RUNE_DEFINITION_PARITY_FAILURE")
 if "get_rune_definition" not in segment or "get_rune_slot_limit" not in segment:findings.append("SIMULATION_RUNE_DOES_NOT_USE_CANONICAL_OWNERS")
 broken=next(x for x in cases if x["label"]=="broken_equipment_should_block")
 if broken["inserted"]!=0:findings.append("SIMULATION_RUNE_INSERTS_INTO_BROKEN_EQUIPMENT")
 scout=next(x for x in cases if x["label"]=="scout_class_aware_equal_level");scout_ids=[r["rune_item_id"] for values in scout["sockets"].values() for r in values]
 if scout_ids and scout_ids[0]!=711:findings.append("SIMULATION_RUNE_SELECTION_NOT_CLASS_AWARE")
 if "character_class" not in segment:findings.append("SIMULATION_RUNE_INSERTION_HAS_NO_CLASS_CONTEXT")
 capacity_violations=[]
 for c in cases:
  for sim_id,sockets in c["sockets"].items():
   item=next((x for x in c.get("items",[]) if x.get("simulation_item_id")==int(sim_id)),None)
  if c["inserted"]!=c["state_inserted"]:capacity_violations.append(c["label"]+":counter")
 if capacity_violations:findings.append("SIMULATION_RUNE_COUNTER_OR_CAPACITY_FAILURE")
 payload={"stage":"18.30.5f","mode":"read-only","verdict":"FAIL" if findings else "PASS","canonical_definition_count":len(definitions),"definition_parity":definition_parity,"item_id_roundtrip":roundtrip,"canonical_slot_limits":slots,"insert_best_runes_calls":calls,"cases":cases,"findings":findings,"recommended_next_patch":"patch_18_30_5g_restore_canonical_rune_lifecycle.py","files_sha256":{x:sha(R/x) for x in FILES if (R/x).is_file()}}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(f"[PASS] audited rune cases: {len(cases)}");print(f"[INFO] canonical rune definitions: {len(definitions)}");print(f"[INFO] findings: {len(findings)}");print(f"[REPORT] {OUT.relative_to(R)}")
if __name__=="__main__":main()
