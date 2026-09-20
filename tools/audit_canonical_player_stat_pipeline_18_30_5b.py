#!/usr/bin/env python3
from __future__ import annotations
import ast,hashlib,json,sys
from dataclasses import asdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
OUT=R/"reports"/"simulation"/"stage_18_30_5b_canonical_player_stat_pipeline_audit.json"
CLASSES=("warrior","knight","scout","rogue","mage","priest");LEVELS=(1,2,5,10)
FILES=("data/player_hp.py","data/player_combat_chances.py","data/defense_policy.py","data/stat_system_config.py","systems/stat_system.py","systems/refine_system.py","systems/simulation/combat_actor_stats.py","systems/simulation/models.py")
def sha(p):h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def source(rel):return (R/rel).read_text(encoding="utf-8")
def imports(rel):
 tree=ast.parse(source(rel));rows=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.ImportFrom):rows.append({"module":n.module,"names":[x.name for x in n.names],"line":n.lineno})
  elif isinstance(n,ast.Import):rows.append({"module":None,"names":[x.name for x in n.names],"line":n.lineno})
 return rows
def canonical(cls,level,sim):
 from data.player_hp import calculate_base_max_hp
 from data.player_combat_chances import calculate_magical_crit_chance,calculate_physical_crit_chance,calculate_dodge_chance
 from systems.stat_system import calculate_magical_attack,calculate_max_mp,calculate_physical_attack,calculate_physical_defense,calculate_magical_defense
 hp=calculate_base_max_hp(level,sim.sta)
 return {"str":sim.str,"dex":sim.dex,"intelligence":sim.intelligence,"wis":sim.wis,"sta":sim.sta,"max_hp":hp,"max_mp":calculate_max_mp(cls,level=level,intelligence=sim.intelligence,wisdom=sim.wis),"attack":calculate_physical_attack(cls,strength=sim.str,dexterity=sim.dex,intelligence=sim.intelligence,wisdom=sim.wis,stamina=sim.sta),"magic_attack":calculate_magical_attack(cls,strength=sim.str,dexterity=sim.dex,intelligence=sim.intelligence,wisdom=sim.wis,stamina=sim.sta),"pdef":calculate_physical_defense(equipment_pdef=0,stamina=sim.sta),"mdef":calculate_magical_defense(equipment_mdef=0,wisdom=sim.wis),"physical_crit":calculate_physical_crit_chance(sim.dex),"magical_crit":calculate_magical_crit_chance(sim.wis),"dodge_equal_dex":calculate_dodge_chance(sim.dex,sim.dex)}
def compare(sim,can):
 sd=asdict(sim);keys=("str","dex","intelligence","wis","sta","max_hp","max_mp","attack","magic_attack","pdef","mdef");return {k:{"simulation":sd[k],"canonical":can[k],"delta":sd[k]-can[k],"parity":"PASS" if sd[k]==can[k] else "FAIL"} for k in keys}
def make_item(item_id,slot,stats,durability=100,refine=0,runes=None):
 from systems.simulation.models import SimulationInventoryItem
 item=SimulationInventoryItem(item_id,900000+item_id,f"fixture-{item_id}","equipment",1,1,slot,1,"common",durability=durability,refine_level=refine,stats=dict(stats))
 item.runes=list(runes or []);return item
def scenario(cls,level,label,item=None):
 from systems.simulation.combat_actor_stats import build_combat_stat_snapshot
 from systems.simulation.models import SimulationEquipment,SimulationInventory
 inv=SimulationInventory();eq=SimulationEquipment()
 if item is not None:inv.items.append(item);eq.slots[item.slot_key]=item.simulation_item_id
 sim=build_combat_stat_snapshot(cls,level,inv,eq);can=canonical(cls,level,sim);cmp=compare(sim,can)
 return {"class":cls,"level":level,"scenario":label,"simulation":asdict(sim),"canonical":can,"comparison":cmp,"failed_stats":[k for k,v in cmp.items() if v["parity"]=="FAIL"],"critical_chances":{"physical":can["physical_crit"],"magical":can["magical_crit"],"dodge_equal_dex":can["dodge_equal_dex"]}}
def main():
 from systems.simulation.models import SimulationRuneSocket
 rows=[]
 for cls in CLASSES:
  for level in LEVELS:rows.append(scenario(cls,level,"empty"))
 probes=[]
 probes.append(scenario("scout",1,"sta_equipment",make_item(1,"chest",{"sta":2,"pdef":3,"mdef":1})))
 probes.append(scenario("scout",1,"dex_weapon",make_item(2,"main_hand",{"dex":2,"weapon_min_damage":2,"weapon_max_damage":4})))
 probes.append(scenario("scout",1,"sta_rune",make_item(3,"chest",{"pdef":1},runes=[SimulationRuneSocket(0,1001,"sta",1)])))
 probes.append(scenario("scout",1,"refined_armor",make_item(4,"chest",{"sta":1,"pdef":2},refine=2)))
 probes.append(scenario("scout",1,"zero_durability",make_item(5,"chest",{"sta":9,"pdef":99,"mdef":99},durability=0)))
 allrows=rows+probes;failed=sorted({k for r in allrows for k in r["failed_stats"]})
 simsrc=source("systems/simulation/combat_actor_stats.py")
 owners={"max_hp":"data.player_hp.calculate_base_max_hp","max_mp":"systems.stat_system.calculate_max_mp","attack":"systems.stat_system.calculate_physical_attack","magic_attack":"systems.stat_system.calculate_magical_attack","pdef":"systems.stat_system.calculate_physical_defense","mdef":"systems.stat_system.calculate_magical_defense","physical_crit":"data.player_combat_chances.calculate_physical_crit_chance","magical_crit":"data.player_combat_chances.calculate_magical_crit_chance","dodge":"data.player_combat_chances.calculate_dodge_chance"}
 usage={k:(v.split('.')[-1] in simsrc) for k,v in owners.items()}
 findings=[]
 for k in failed:findings.append(f"SIMULATION_{k.upper()}_PARITY_FAILURE")
 for k,v in usage.items():
  if not v:findings.append(f"SIMULATION_DOES_NOT_USE_CANONICAL_{k.upper()}_OWNER")
 payload={"stage":"18.30.5b","mode":"read-only","verdict":"FAIL" if findings else "PASS","canonical_owners":owners,"simulation_owner_usage":usage,"empty_state_matrix":rows,"equipment_rune_refine_durability_probes":probes,"failed_stats":failed,"findings":findings,"simulation_imports":imports("systems/simulation/combat_actor_stats.py"),"files_sha256":{x:sha(R/x) for x in FILES},"recommended_next_patch":"patch_18_30_5c_restore_canonical_player_stat_parity.py"}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(f"[PASS] audited scenarios: {len(allrows)}")
 print(f"[INFO] failed stats: {', '.join(failed) if failed else 'none'}")
 print(f"[INFO] findings: {len(findings)}")
 print(f"[REPORT] {OUT.relative_to(R)}")
if __name__=="__main__":main()
