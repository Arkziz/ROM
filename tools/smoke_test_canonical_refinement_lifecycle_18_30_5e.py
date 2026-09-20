from __future__ import annotations
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from systems.simulation.meta_progression import SimulationMetaProgressionService
from systems.simulation.models import SimulationEquipment,SimulationInventory,SimulationInventoryItem
class Rng:
 def __init__(self,rolls):self.rolls=list(rolls);self.calls=0
 def randint(self,a,b):self.calls+=1;return self.rolls.pop(0)
def equip(sim_id,slot,level=0,item_level=1,rarity="common",durability=100):return SimulationInventoryItem(sim_id,10000+sim_id,f"eq-{sim_id}","equipment",1,1,slot,item_level,rarity,durability=durability,refine_level=level,item_subtype="weapon" if slot=="main_hand" else "",stats={"weapon_min_damage":10,"weapon_max_damage":20} if slot=="main_hand" else {"pdef":2})
def stone(q):return SimulationInventoryItem(99000,601,"stone","material",q,999)
def service(items,slots,rolls):
 inv=SimulationInventory();inv.items=list(items);eq=SimulationEquipment();eq.slots.update(slots);rng=Rng(rolls);return SimulationMetaProgressionService(inv,eq,rng),rng
# Exact 50% is allowed and all available stones are used while the next chance stays >=50.
w=equip(1,"main_hand",6);svc,rng=service([w,stone(2)],{"main_hand":1},[50]);assert svc.refine_best() is True;assert w.refine_level==7 and svc._qty(601)==1 and svc.state.refine_attempts==1 and svc.state.refine_successes==1 and rng.calls==1
# Below 50%, max level and broken equipment are blocked without stone or RNG consumption.
for target in (equip(2,"main_hand",7),equip(3,"chest",4),equip(4,"main_hand",10),equip(5,"chest",6),equip(6,"main_hand",0,durability=0)):
 svc,rng=service([target,stone(1)],{target.slot_key:target.simulation_item_id},[1]);before=target.refine_level;assert svc.refine_best() is False;assert target.refine_level==before and svc._qty(601)==1 and svc.state.refine_attempts==0 and rng.calls==0
# Canonical protected failure levels do not degrade.
for target in (equip(7,"main_hand",3),equip(8,"chest",2)):
 svc,rng=service([target,stone(1)],{target.slot_key:target.simulation_item_id},[100]);before=target.refine_level;assert svc.refine_best() is False;assert target.refine_level==before and svc._qty(601)==0 and svc.state.refine_attempts==1
# Canonical degrading failure levels use production owner.
for target,expected in ((equip(9,"main_hand",4),3),(equip(10,"chest",3),2)):
 svc,rng=service([target,stone(1)],{target.slot_key:target.simulation_item_id},[100]);assert svc.refine_best() is False;assert target.refine_level==expected
# Multi-stone loop, canonical rarity rank, and item-level priority.
a=equip(11,"main_hand",0,item_level=2,rarity="common");b=equip(12,"chest",0,item_level=1,rarity="epic");svc,rng=service([a,b,stone(3)],{"main_hand":11,"chest":12},[1,1,1]);assert svc.refine_best() is True;assert a.refine_level==3 and b.refine_level==0 and svc._qty(601)==0 and svc.state.refine_attempts==3
c=equip(13,"main_hand",0,item_level=1,rarity="rare");d=equip(14,"chest",0,item_level=1,rarity="epic");svc,rng=service([c,d,stone(1)],{"main_hand":13,"chest":14},[1]);assert svc.refine_best() is True;assert d.refine_level==1 and c.refine_level==0
print("[PASS] canonical refinement owner, 50% gate, failure levels, selection and multi-stone lifecycle")
