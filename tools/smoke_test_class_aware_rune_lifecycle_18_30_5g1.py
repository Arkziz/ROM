from __future__ import annotations
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from data.runes import get_rune_definition
from systems.simulation.meta_progression import SimulationMetaProgressionService
from systems.simulation.models import SimulationEquipment,SimulationInventory,SimulationInventoryItem,SimulationRuneSocket
class Rng:
 def randint(self,a,b):return a
def eq(sim_id,slot,durability=100,runes=None):
 x=SimulationInventoryItem(sim_id,10000+sim_id,f"eq-{sim_id}","equipment",1,1,slot,1,"common",durability=durability);x.runes=list(runes or []);return x
def rune(sim_id,item_id,qty=1):
 d=get_rune_definition(item_id);return SimulationInventoryItem(sim_id,item_id,d["name"],"rune",qty,50)
def svc(items,slots):
 inv=SimulationInventory();inv.items=list(items);equipment=SimulationEquipment();equipment.slots.update(slots);return SimulationMetaProgressionService(inv,equipment,Rng()),inv
# Scout chooses DEX before equal-level STR when only one socket is available.
e=eq(1,"ring");s,inv=svc([e,rune(100,701),rune(101,711)],{"ring":1});assert s.insert_best_runes("scout")==1;assert e.runes[0].rune_item_id==711;assert s._qty(701)==1
# Mage chooses INT before WIS and unrelated physical stats at equal level.
e=eq(2,"ring");s,inv=svc([e,rune(102,716),rune(103,721),rune(104,701)],{"ring":2});assert s.insert_best_runes("mage")==1;assert e.runes[0].rune_item_id==716
# Priest class identity prioritizes WIS before INT.
e=eq(3,"ring");s,inv=svc([e,rune(105,716),rune(106,721)],{"ring":3});assert s.insert_best_runes("priest")==1;assert e.runes[0].rune_item_id==721
# Broken and unequipped equipment do not consume runes.
for e,slots in ((eq(4,"main_hand",0),{"main_hand":4}),(eq(5,"main_hand"),{})):
 s,inv=svc([e,rune(107,711)],slots);assert s.insert_best_runes("scout")==0;assert s._qty(711)==1 and not e.runes
# Existing sockets and canonical capacities remain intact.
old=[SimulationRuneSocket(0,701,"STR",1),SimulationRuneSocket(1,706,"STA",1)];e=eq(6,"chest",runes=old);s,inv=svc([e,rune(108,711,3)],{"chest":6});assert s.insert_best_runes("scout")==1;assert len(e.runes)==3 and e.runes[2].slot_index==2 and s._qty(711)==2
# Fusion conservation: 3 runes + 1 token -> 1 next-level rune.
src=rune(109,711,3);token=SimulationInventoryItem(110,726,"token","material",1,999);s,inv=svc([src,token],{});assert s.fuse_available_runes()==1;assert s._qty(711)==0 and s._qty(712)==1 and s._qty(726)==0 and s.state.rune_fusions==1
print("[PASS] approved class-identity rune priority, durability gate, capacities, counters and fusion conservation")
