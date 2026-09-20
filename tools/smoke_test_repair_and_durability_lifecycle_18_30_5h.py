from __future__ import annotations
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from systems.equipment_system import calculate_repair_cost
from systems.simulation.behavior_policy import BehaviorPolicy
from systems.simulation.models import SimulationEquipment,SimulationInventory,SimulationInventoryItem
from systems.simulation.survival_state import SimulationSurvivalService

def eq(sim_id,slot,durability,rarity="common"):
 return SimulationInventoryItem(sim_id,10000+sim_id,f"eq-{sim_id}","equipment",1,1,slot,1,rarity,durability=durability)
def service(items,slots):
 inv=SimulationInventory();inv.items=list(items);equipment=SimulationEquipment();equipment.slots.update(slots);return SimulationSurvivalService(inv,equipment)
policy=BehaviorPolicy();assert policy.repair_threshold==15
assert policy.maintenance([16],40) is None
assert policy.maintenance([15],40).reason=="equipped_durability_at_or_below_15"
assert policy.maintenance([14],40).reason=="equipped_durability_at_or_below_15"
assert policy.maintenance([],2).reason=="inventory_reserve_reached"
# Death damages every equipped item by exactly 5, never below zero, and ignores unequipped items.
a=eq(1,"chest",100);b=eq(2,"gloves",5);c=eq(3,"ring",80);svc=service([a,b,c],{"chest":1,"gloves":2})
r=svc.damage_on_death();assert (a.durability,b.durability,c.durability)==(95,0,80);assert r.changed==2 and r.broken==1 and r.item_ids==[1,2]
r=svc.damage_on_death();assert (a.durability,b.durability)==(90,0);assert r.changed==1 and r.broken==0
# Boundary: 16 is not repaired; 15 and 14 are repaired with canonical production cost.
a=eq(4,"chest",16,"rare");b=eq(5,"gloves",15,"common");svc=service([a,b],{"chest":4,"gloves":5});cost=float(calculate_repair_cost(15,"common"));gold,result=svc.urgent_repair(100.0)
assert a.durability==16 and b.durability==100;assert result.repaired==1 and result.cost==round(cost,2) and result.skipped_for_gold==0;assert gold==round(100.0-cost,2)
# Insufficient gold preserves durability and reports one skipped candidate.
a=eq(6,"chest",0,"epic");svc=service([a],{"chest":6});needed=float(calculate_repair_cost(0,"epic"));gold,result=svc.urgent_repair(max(0.0,needed-0.01));assert a.durability==0 and result.repaired==0 and result.skipped_for_gold==1 and result.cost==0.0
# Exact gold succeeds and reaches 100 durability.
gold,result=svc.urgent_repair(needed);assert gold==0.0 and a.durability==100 and result.repaired==1 and result.cost==round(needed,2)
# Multiple candidates are processed deterministically by simulation_item_id; affordable ones repair, others remain.
a=eq(9,"chest",10,"common");b=eq(8,"gloves",10,"common");svc=service([a,b],{"chest":9,"gloves":8});one=float(calculate_repair_cost(10,"common"));gold,result=svc.urgent_repair(one);assert b.durability==100 and a.durability==10;assert result.item_ids==[8] and result.skipped_for_gold==1
print("[PASS] <=15% repair boundary, canonical cost, death wear, insufficient gold and deterministic partial repair")
