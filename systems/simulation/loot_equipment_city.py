from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

from systems import drop_system
from .equipment_service import SimulationEquipmentService
from .inventory_engine import InventoryAward, SimulationInventoryEngine
from .models import SimulationEquipment, SimulationInventory
from .rng import SimulationRng

SLOTS=("main_hand","off_hand","helmet","shoulders","chest","gloves","legs","boots","necklace","ring")
ARMOR_BY_CLASS={"warrior":"chain","knight":"plate","scout":"leather","rogue":"leather","mage":"cloth","priest":"cloth"}
RARITY_MULT={"common":1.0,"uncommon":1.35,"rare":1.85,"epic":2.60}
SELL_MULT={"common":0.30,"uncommon":0.90,"rare":2.25,"epic":6.00}
POTIONS={401:("HP potion",38,"hp_potion"),402:("Large HP potion",77,"hp_potion"),403:("MP potion",38,"mp_potion"),404:("Large MP potion",77,"mp_potion")}

@dataclass
class VictoryLootResult:
    rolled:int=0;awarded:int=0;lost:int=0;full_bag_events:int=0;equipment:int=0;stacks:int=0;records:list=None
    def __post_init__(self):
        if self.records is None:self.records=[]

@dataclass
class CityResult:
    sold_items:int=0;sold_quantity:int=0;gold_received:float=0.0;equipped:int=0;rejected:int=0;records:list=None
    def __post_init__(self):
        if self.records is None:self.records=[]

class SimulationLootEquipmentCityService:
    def __init__(self, character_class:str, inventory:SimulationInventory, equipment:SimulationEquipment, rng:SimulationRng):
        self.character_class=character_class;self.inventory=inventory;self.equipment=equipment;self.rng=rng;self.engine=SimulationInventoryEngine(inventory);self.equipment_service=SimulationEquipmentService(character_class,inventory,equipment)

    def _equipment_award(self,mob:Dict[str,Any],payload:Dict[str,Any]):
        level=int(mob.get("level",1));rarity=str(payload.get("rarity","common"));slot=self.rng.choice(SLOTS);mult=RARITY_MULT[rarity]
        stats={};armor="";hands=1
        if slot=="main_hand":
            hands=2 if self.rng.random()<0.35 else 1;stats["weapon_min_damage"]=max(1,int(level*1.2*mult));stats["weapon_max_damage"]=max(2,int(level*2.0*mult));stats["str" if self.character_class in {"warrior","knight"} else "dex" if self.character_class in {"scout","rogue"} else "int"]=max(1,int(level*.7*mult))
        elif slot=="off_hand":stats["pdef" if self.character_class in {"warrior","knight","scout","rogue"} else "mdef"]=max(1,int(level*mult))
        else:
            if slot in {"helmet","shoulders","chest","gloves","legs","boots"}:armor=ARMOR_BY_CLASS[self.character_class]
            stats["pdef"]=max(1,int(level*.7*mult));stats["mdef"]=max(1,int(level*.4*mult));stats["sta"]=max(1,int(level*.3*mult))
        item_id=900000+self.inventory.next_simulation_item_id
        return InventoryAward(item_id,f"{rarity} {slot} L{level}","equipment",1,1,slot,level,rarity,round(level*SELL_MULT[rarity],2),{"stats":stats,"armor_type":armor,"weapon_hands":hands})

    def _stack_award(self,item_id:int,quantity:int=1):
        if item_id in POTIONS:
            name,restore,kind=POTIONS[item_id];return InventoryAward(item_id,name,"potion",quantity,99,sell_price=round(restore*.05,2),payload={"restore":restore,"item_subtype":kind})
        return InventoryAward(item_id,f"Item {item_id}","material",quantity,999,sell_price=1.0)

    def process_victory(self,mob:Dict[str,Any]):
        out=VictoryLootResult()
        results=[
            drop_system.roll_central_equipment_drop(mob,self.rng.random),
            drop_system.roll_central_refine_stone_drop(mob,self.rng.random),
            drop_system.roll_central_rune_drop(mob,self.rng.random),
            drop_system.roll_central_potion_drop(mob,self.rng.random),
            drop_system.roll_central_trophy_simple(mob,self.rng.random,self.rng.choice),
        ]
        for row in results:
            if not row.get("rolled"):continue
            payload=row.get("payload") or {};resolver=payload.get("resolver")
            award=None
            if resolver=="equipment":award=self._equipment_award(mob,payload);out.equipment+=1
            elif resolver=="rune":
                stat=str(payload.get("stat","STA")).upper();level=int(payload.get("level",1));item_id=701+("STR","STA","DEX","INT","WIS").index(stat)*5+level-1;award=self._stack_award(item_id)
            elif payload.get("item_id") is not None:award=self._stack_award(int(payload["item_id"]),int(payload.get("quantity",1)))
            if award is None:continue
            applied=self.engine.award(award,True);out.rolled+=award.quantity;out.awarded+=applied.awarded;out.lost+=applied.lost
            if applied.lost:out.full_bag_events+=1
            out.records.append({"item_id": award.item_id, "name": award.name, "category": award.category, "rarity": award.rarity, "found": award.quantity, "awarded": applied.awarded, "lost_due_capacity": applied.lost, "destination": "inventory" if applied.awarded else "lost_due_capacity"})
            if not award.is_equipment:out.stacks+=applied.awarded
        return out

    def equip_upgrades(self):
        equipped=rejected=0
        for item in list(self.inventory.items):
            if not item.is_equipment or item.simulation_item_id in self.equipment.slots.values():continue
            decision=self.equipment_service.decide(item.simulation_item_id)
            if decision.action=="equip":self.equipment_service.apply(decision);equipped+=1
            else:rejected+=1
        return equipped,rejected

    def city_maintenance(self,gold:float):
        equipped,rejected=self.equip_upgrades();protected={value for value in self.equipment.slots.values() if value}
        sold=[];received=0.0;quantity=0
        for item in list(self.inventory.items):
            if item.simulation_item_id in protected:continue
            if item.category=="equipment" or item.category=="trash":
                received+=float(item.sell_price)*item.quantity;quantity+=item.quantity;sold.append(item)
        for item in sold:self.inventory.items.remove(item)
        self.inventory.validate()
        records=[{"simulation_item_id": item.simulation_item_id, "item_id": item.item_id, "name": item.name, "category": item.category, "rarity": item.rarity, "quantity": item.quantity, "destination": "sold", "gold": round(float(item.sell_price)*item.quantity,2)} for item in sold]
        return round(gold+received,2),CityResult(len(sold),quantity,round(received,2),equipped,rejected,records)
