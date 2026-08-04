from dataclasses import dataclass, field
from .models import SimulationInventory, SimulationInventoryItem

@dataclass
class InventoryAward:
    item_id:int; name:str; category:str; quantity:int=1; max_stack:int=1; slot_key:str=''; item_level:int=1; rarity:str='common'; sell_price:float=0.0; payload:dict=field(default_factory=dict)
    @property
    def is_equipment(self): return self.category=='equipment'

@dataclass
class InventoryAwardResult:
    awarded:int; lost:int; new_slots:int; merged:int; reason:str; created_ids:list=field(default_factory=list)

class SimulationInventoryEngine:
    def __init__(self, inventory:SimulationInventory): self.inventory=inventory
    def required_new_slots(self,a):
        left=int(a.quantity)
        if a.is_equipment:return left
        for x in self.inventory.items:
            if x.item_id==a.item_id and not x.is_equipment and x.max_stack==a.max_stack:left=max(0,left-x.free_stack_space)
        return 0 if left<=0 else (left+a.max_stack-1)//a.max_stack
    def award(self,a,all_or_nothing=True):
        need=self.required_new_slots(a)
        if all_or_nothing and need>self.inventory.free_slots:return InventoryAwardResult(0,a.quantity,0,0,'inventory_full')
        left=int(a.quantity); merged=0; ids=[]
        if not a.is_equipment:
            for x in self.inventory.items:
                if left<=0:break
                if x.item_id==a.item_id and not x.is_equipment and x.max_stack==a.max_stack:
                    n=min(left,x.free_stack_space);x.quantity+=n;left-=n;merged+=n
        while left>0 and self.inventory.free_slots>0:
            n=1 if a.is_equipment else min(left,a.max_stack)
            x=SimulationInventoryItem(self.inventory.allocate_id(),a.item_id,a.name,a.category,n,1 if a.is_equipment else a.max_stack,a.slot_key,a.item_level,a.rarity,sell_price=a.sell_price,stats=dict(a.payload.get('stats',{})))
            self.inventory.items.append(x);ids.append(x.simulation_item_id);left-=n
        self.inventory.validate();return InventoryAwardResult(a.quantity-left,left,len(ids),merged,'awarded' if left==0 else 'partial_capacity',ids)
