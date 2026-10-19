"""Audited V1-parity equipment-slot value objects and policy inputs."""
from __future__ import annotations
from dataclasses import dataclass

SLOT_KEYS=("main_hand","off_hand","helmet","shoulders","chest","gloves","legs","boots","necklace","ring")
@dataclass(frozen=True,slots=True)
class EquipmentItemPolicy:
    inventory_id:int; owner_user_id:int; slot_key:str; required_level:int=1
    allowed_classes:tuple[str,...]=(); weapon_hands:int=1; durability:int=100
    def __post_init__(self):
        if self.inventory_id<=0 or self.owner_user_id<=0: raise ValueError("equipment_identity_invalid")
        if self.slot_key not in SLOT_KEYS: raise ValueError("equipment_slot_invalid")
        if self.required_level<1: raise ValueError("required_level_invalid")
        if self.weapon_hands not in (1,2): raise ValueError("weapon_hands_invalid")
        if self.durability<0: raise ValueError("durability_negative")
@dataclass(frozen=True,slots=True)
class EquipmentSlot:
    owner_user_id:int; slot_key:str; inventory_id:int
    def __post_init__(self):
        if self.owner_user_id<=0 or self.inventory_id<=0: raise ValueError("equipment_identity_invalid")
        if self.slot_key not in SLOT_KEYS: raise ValueError("equipment_slot_invalid")
