from dataclasses import asdict,dataclass,field
from systems import drop_system
from .inventory_engine import InventoryAward,SimulationInventoryEngine

@dataclass
class DropProcessResult:
    rolled:int=0;awarded:int=0;lost:int=0;full_bag_events:int=0;lost_value:float=0.0;results:list=field(default_factory=list)

class SimulationDropInventoryEngine:
    def __init__(self,inventory,rng,item_resolver):self.inventory=inventory;self.rng=rng;self.item_resolver=item_resolver;self.inventory_engine=SimulationInventoryEngine(inventory)
    def roll_enemy(self,mob,rules=None):
        if rules is None:return drop_system.roll_enemy_drops(mob,self.rng.random)
        # Explicit simulation fixtures are rolled one by one. Full production-table
        # validation remains active when rules=None.
        return [drop_system.roll_drop_rule(rule,mob,self.rng.random) for rule in rules]
    def process_enemy(self,mob,rules=None):
        out=DropProcessResult()
        for row in self.roll_enemy(mob,rules):
            entry=dict(row);payload=entry.get('payload') or {};item_id=payload.get('item_id')
            if not entry.get('rolled') or item_id is None:out.results.append(entry);continue
            meta=dict(self.item_resolver(int(item_id)) or {})
            if not meta:out.results.append(entry);continue
            a=InventoryAward(int(item_id),str(meta.get('name',item_id)),str(meta.get('category','material')),int(payload.get('quantity',1)),int(meta.get('max_stack',1)),str(meta.get('slot_key','')),int(meta.get('item_level',1)),str(meta.get('rarity','common')),float(meta.get('sell_price',0)),meta)
            out.rolled+=a.quantity;applied=self.inventory_engine.award(a,True);entry['simulation_inventory']=asdict(applied)
            if applied.awarded:out.awarded+=applied.awarded;entry['awarded']=True;entry['lost']=False
            else:out.lost+=applied.lost;out.full_bag_events+=1;out.lost_value+=applied.lost*a.sell_price;entry['awarded']=False;entry['lost']=True;entry['reason']='inventory_full'
            out.results.append(entry)
        return out
