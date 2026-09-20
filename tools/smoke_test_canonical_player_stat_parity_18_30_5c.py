from __future__ import annotations
import subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from systems.simulation.combat_actor_stats import build_battle_actor,build_combat_stat_snapshot
from systems.simulation.models import SimulationEquipment,SimulationInventory,SimulationInventoryItem,SimulationRuneSocket
from data.player_hp import calculate_base_max_hp
from systems.stat_system import calculate_magical_attack,calculate_max_mp,calculate_physical_attack,calculate_physical_defense,calculate_magical_defense
CLASSES=("warrior","knight","scout","rogue","mage","priest")
def expected(c,l,s,pdef=0,mdef=0):
 kw=dict(strength=s.str,dexterity=s.dex,intelligence=s.intelligence,wisdom=s.wis,stamina=s.sta)
 return calculate_base_max_hp(l,s.sta),calculate_max_mp(c,level=l,intelligence=s.intelligence,wisdom=s.wis) if s.resource_type=="mana" else 0,calculate_physical_attack(c,**kw),calculate_magical_attack(c,**kw),calculate_physical_defense(equipment_pdef=pdef,stamina=s.sta),calculate_magical_defense(equipment_mdef=mdef,wisdom=s.wis)
for c in CLASSES:
 for l in (1,2,5,10):
  s=build_combat_stat_snapshot(c,l,SimulationInventory(),SimulationEquipment());assert (s.max_hp,s.max_mp,s.attack,s.magic_attack,s.pdef,s.mdef)==expected(c,l,s),(c,l,s,expected(c,l,s))
s=build_combat_stat_snapshot("scout",1,SimulationInventory(),SimulationEquipment());assert s.max_hp==130 and s.attack==12 and s.magic_attack==2
inv=SimulationInventory();eq=SimulationEquipment();item=SimulationInventoryItem(1,920001,"fixture","equipment",1,1,"chest",1,"common",durability=100,refine_level=2,stats={"sta":1,"pdef":2,"mdef":1});item.runes=[SimulationRuneSocket(0,1001,"sta",1)];inv.items.append(item);eq.slots["chest"]=item.simulation_item_id;s=build_combat_stat_snapshot("scout",1,inv,eq);base=calculate_base_max_hp(1,12);assert s.max_hp==round(base*1.01);assert (s.pdef,s.mdef)==expected("scout",1,s,2,1)[4:]
item.durability=0;s0=build_combat_stat_snapshot("scout",1,inv,eq);assert s0.max_hp==130 and s0.sta==10 and s0.pdef==3 and s0.mdef==3
actor=build_battle_actor("scout",1,SimulationInventory(),SimulationEquipment(),current_hp=999);assert actor.max_hp==130 and actor.hp==130
actor=build_battle_actor("scout",1,SimulationInventory(),SimulationEquipment(),current_hp=80);assert actor.hp==80 and actor.max_hp==130
runner=R/"tools"/"run_class_progression_simulation.py";x=subprocess.run([sys.executable,str(runner),"--class","scout","--target-level","2","--seed","2","--max-days","30"],cwd=R,text=True,capture_output=True);assert x.returncode==0,x.stderr
print("[PASS] canonical Max HP, PATK, MATK and current HP semantics")
