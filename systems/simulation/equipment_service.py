from __future__ import annotations
from typing import Dict, List
from .equipment_policy import EquipmentDecision, evaluate_candidate
from .models import SimulationEquipment, SimulationInventory

class SimulationEquipmentService:
    def __init__(self, character_class: str, inventory: SimulationInventory, equipment: SimulationEquipment):
        self.character_class=character_class; self.inventory=inventory; self.equipment=equipment

    def decide(self, simulation_item_id: int) -> EquipmentDecision:
        item=next(item for item in self.inventory.items if item.simulation_item_id==simulation_item_id)
        return evaluate_candidate(self.character_class,item,self.inventory,self.equipment)

    def apply(self, decision: EquipmentDecision) -> None:
        if decision.action != "equip": return
        item=next(item for item in self.inventory.items if item.simulation_item_id==decision.candidate_id)
        for slot,value in list(self.equipment.slots.items()):
            if value in decision.replaced_ids:self.equipment.slots[slot]=None
        self.equipment.slots[item.slot_key]=item.simulation_item_id
        if item.slot_key=="main_hand" and int(item.weapon_hands or 1)==2:self.equipment.slots["off_hand"]=None
