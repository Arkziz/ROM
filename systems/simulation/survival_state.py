from __future__ import annotations
from dataclasses import dataclass

from data.mana_policy import apply_post_combat_mp_floor_value
from typing import Dict, Iterable, List

from .canonical_rules import call_rule
from .models import SimulationEquipment, SimulationInventory

MANA_CLASSES = {"mage", "priest"}

@dataclass
class PersistentCombatState:
    hp: int
    max_hp: int
    mp: int
    max_mp: int

    def clamp(self):
        self.hp=max(0,min(int(self.hp),int(self.max_hp)))
        self.mp=max(0,min(int(self.mp),int(self.max_mp)))

    def passive_hp_regen(self, minutes: int) -> int:
        ticks=max(0,int(minutes)); per_tick=max(1,int(self.max_hp*0.10)); before=self.hp
        self.hp=min(self.max_hp,self.hp+ticks*per_tick)
        return self.hp-before

    def restore_mp_after_combat(self) -> int:
        """Apply the canonical 50% floor without adding or reducing current MP."""
        before = self.mp
        self.mp = apply_post_combat_mp_floor_value(self.mp, self.max_mp)
        return self.mp - before

    def apply_death(self) -> None:
        self.hp=1
        self.mp=self.max_mp

@dataclass
class DurabilityResult:
    changed: int
    broken: int
    item_ids: List[int]

@dataclass
class RepairResult:
    repaired: int
    cost: float
    skipped_for_gold: int
    item_ids: List[int]

class SimulationSurvivalService:
    def __init__(self, inventory: SimulationInventory, equipment: SimulationEquipment):
        self.inventory=inventory;self.equipment=equipment

    def equipped_items(self):
        ids={value for value in self.equipment.slots.values() if value is not None}
        return [item for item in self.inventory.items if item.simulation_item_id in ids]

    def damage_on_death(self) -> DurabilityResult:
        changed=[];broken=0
        for item in self.equipped_items():
            old=item.durability;item.durability=max(0,old-5)
            if item.durability!=old:changed.append(item.simulation_item_id)
            if old>0 and item.durability==0:broken+=1
        return DurabilityResult(len(changed),broken,changed)

    def urgent_repair(self, gold: float, threshold: int=15) -> tuple[float,RepairResult]:
        candidates=[item for item in self.equipped_items() if item.durability<=int(threshold)]
        repaired=[];cost=0.0;skipped=0
        for item in sorted(candidates,key=lambda x:x.simulation_item_id):
            item_cost=float(call_rule("repair_cost",item.durability,item.rarity))
            if gold+1e-9 < item_cost:
                skipped+=1;continue
            gold=round(gold-item_cost,2);cost=round(cost+item_cost,2);item.durability=100;repaired.append(item.simulation_item_id)
        return gold,RepairResult(len(repaired),cost,skipped,repaired)
