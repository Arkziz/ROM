#!/usr/bin/env python3
from __future__ import annotations
import ast,hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
OUT=R/"reports"/"simulation"/"stage_18_30_5d_canonical_refinement_lifecycle_audit.json"
FILES=("systems/refine_system.py","systems/simulation/meta_progression.py","systems/simulation/models.py","systems/simulation/combat_actor_stats.py")
def sha(p):h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def item(item_id,sim_id,slot,level=0,item_level=1,rarity="common"):
 from systems.simulation.models import SimulationInventoryItem
 return SimulationInventoryItem(item_id,sim_id,f"fixture-{sim_id}","equipment",1,1,slot,1,rarity,durability=100,refine_level=level,stats={"weapon_min_damage":10,"weapon_max_damage":20} if slot=="main_hand" else {"pdef":2})
def stone(qty):
 from systems.simulation.models import SimulationInventoryItem
 return SimulationInventoryItem(601,999001,"Камінь Посилення","material",qty,999,"",1,"common")
class FixedRng:
 def __init__(self,roll):self.roll=roll
 def randint(self,a,b):return self.roll
def run_case(label,target,roll=1,stones=1,extras=()):
 from systems.simulation.meta_progression import SimulationMetaProgressionService
 from systems.simulation.models import SimulationEquipment,SimulationInventory
 inv=SimulationInventory();eq=SimulationEquipment();inv.items.extend([target,*extras,stone(stones)]);eq.slots[target.slot_key]=target.simulation_item_id
 for x in extras:
  if x.slot_key and x.slot_key not in eq.slots:continue
  if x.slot_key:eq.slots[x.slot_key]=x.simulation_item_id
 svc=SimulationMetaProgressionService(inv,eq,FixedRng(roll));before={"level":target.refine_level,"stones":svc._qty(601)};returned=svc.refine_best();after={"level":target.refine_level,"stones":svc._qty(601),"attempts":svc.state.refine_attempts,"successes":svc.state.refine_successes}
 return {"label":label,"slot":target.slot_key,"before":before,"roll":roll,"returned":returned,"after":after}
def main():
 import systems.refine_system as prod
 import systems.simulation.meta_progression as sim
 weapon={i:prod.get_refine_success_chance("weapon",i) for i in range(0,11)};armor={i:prod.get_refine_success_chance("armor",i) for i in range(0,7)}
 table_parity={"weapon":weapon==sim.WEAPON_REFINE_SUCCESS_CHANCES,"armor":armor==sim.ARMOR_REFINE_SUCCESS_CHANCES}
 boundary={"weapon":{"last_allowed_level":max(i for i,c in weapon.items() if c>=50),"first_blocked_level":min(i for i,c in weapon.items() if c<50)},"armor":{"last_allowed_level":max(i for i,c in armor.items() if c>=50),"first_blocked_level":min(i for i,c in armor.items() if c<50)}}
 cases=[]
 cases.append(run_case("weapon_50_percent_allowed",item(100,1,"main_hand",6),roll=50))
 cases.append(run_case("weapon_below_50_should_block",item(101,2,"main_hand",7),roll=1))
 cases.append(run_case("armor_50_percent_allowed",item(102,3,"chest",3),roll=50))
 cases.append(run_case("armor_below_50_should_block",item(103,4,"chest",4),roll=1))
 cases.append(run_case("weapon_failure_protected_level_3",item(104,5,"main_hand",3),roll=100))
 cases.append(run_case("armor_failure_protected_level_2",item(105,6,"chest",2),roll=100))
 cases.append(run_case("weapon_failure_degrade_level_4",item(106,7,"main_hand",4),roll=100))
 cases.append(run_case("armor_failure_degrade_level_3",item(107,8,"chest",3),roll=100))
 cases.append(run_case("weapon_max_level_should_block",item(108,9,"main_hand",10),roll=1))
 cases.append(run_case("armor_max_level_should_block",item(109,10,"chest",6),roll=1))
 src=(R/"systems/simulation/meta_progression.py").read_text(encoding="utf-8");tree=ast.parse(src);refine=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="refine_best")
 called=sorted({ast.unparse(n.func) for n in ast.walk(refine) if isinstance(n,ast.Call)});source_segment=ast.get_source_segment(src,refine)
 findings=[]
 if not all(table_parity.values()):findings.append("SIMULATION_REFINE_CHANCE_TABLE_PARITY_FAILURE")
 if "get_refine_success_chance" not in source_segment:findings.append("SIMULATION_REFINE_DOES_NOT_USE_CANONICAL_CHANCE_OWNER")
 if ">=50" not in source_segment.replace(" ","") and ">= 50" not in source_segment:findings.append("SIMULATION_REFINE_MISSING_50_PERCENT_GATE")
 expected={
  "weapon_below_50_should_block":lambda x:x["after"]["attempts"]==0 and x["after"]["stones"]==1,
  "armor_below_50_should_block":lambda x:x["after"]["attempts"]==0 and x["after"]["stones"]==1,
  "weapon_failure_protected_level_3":lambda x:x["after"]["level"]==3,
  "armor_failure_protected_level_2":lambda x:x["after"]["level"]==2,
  "weapon_max_level_should_block":lambda x:x["after"]["attempts"]==0,
  "armor_max_level_should_block":lambda x:x["after"]["attempts"]==0,
 }
 violations=[]
 for c in cases:
  fn=expected.get(c["label"])
  if fn and not fn(c):violations.append(c["label"])
 if any("below_50" in x for x in violations):findings.append("SIMULATION_REFINE_ATTEMPTS_BELOW_50_PERCENT")
 if any("protected" in x for x in violations):findings.append("SIMULATION_REFINE_FAILURE_LEVEL_PARITY_FAILURE")
 if any("max_level" in x for x in violations):findings.append("SIMULATION_REFINE_ATTEMPTS_AT_MAX_LEVEL")
 # Selection probe: higher item level must win; equal level needs stable score, not lexical rarity.
 a=item(201,20,"main_hand",0,item_level=2,rarity="common");b=item(202,21,"chest",0,item_level=1,rarity="epic");selection=run_case("selection_prefers_item_level",a,roll=1,extras=(b,))
 payload={"stage":"18.30.5d","mode":"read-only","verdict":"FAIL" if findings else "PASS","canonical_chances":{"weapon":weapon,"armor":armor},"simulation_tables":{"weapon":sim.WEAPON_REFINE_SUCCESS_CHANCES,"armor":sim.ARMOR_REFINE_SUCCESS_CHANCES},"table_parity":table_parity,"fifty_percent_boundary":boundary,"refine_best_calls":called,"cases":cases,"contract_violations":violations,"selection_probe":selection,"findings":findings,"recommended_next_patch":"patch_18_30_5e_restore_canonical_refinement_lifecycle.py","files_sha256":{x:sha(R/x) for x in FILES}}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(f"[PASS] audited refinement cases: {len(cases)+1}");print(f"[INFO] table parity: weapon={table_parity['weapon']}, armor={table_parity['armor']}");print(f"[INFO] contract violations: {', '.join(violations) if violations else 'none'}");print(f"[INFO] findings: {len(findings)}");print(f"[REPORT] {OUT.relative_to(R)}")
if __name__=="__main__":main()
