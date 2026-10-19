"""V1-parity value objects for canonical equipment generation."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

JEWELRY_SLOTS=frozenset({"necklace","ring"})
WEAPON_SLOTS=frozenset({"main_hand","off_hand"})
ARMOR_SLOTS=frozenset({"helmet","shoulders","chest","gloves","legs","boots"})
ALL_GENERATED_SLOTS=WEAPON_SLOTS|ARMOR_SLOTS|JEWELRY_SLOTS

class EquipmentGenerationSource(StrEnum):
    SHOP="shop"; LOOT="loot"; DEV="dev"; SIMULATOR="simulator"

@dataclass(frozen=True,slots=True)
class EquipmentGenerationRequest:
    source:EquipmentGenerationSource
    item_level:int
    slot_key:str
    rarity:str
    character_class:str|None=None
    armor_type:str|None=None
    identity_hint:str|None=None
    def __post_init__(self)->None:
        if self.item_level<1:raise ValueError("item_level_invalid")
        if self.slot_key not in ALL_GENERATED_SLOTS:raise ValueError("slot_key_invalid")
        if not self.rarity.strip():raise ValueError("rarity_invalid")
        if self.source is EquipmentGenerationSource.SHOP and not self.character_class:raise ValueError("shop_character_class_required")
        if self.slot_key in ARMOR_SLOTS and not self.armor_type:raise ValueError("armor_type_required")
        if self.slot_key in JEWELRY_SLOTS and self.armor_type is not None:raise ValueError("jewelry_armor_type_forbidden")

@dataclass(frozen=True,slots=True)
class EquipmentIdentity:
    slot_key:str
    item_subtype:str
    display_name:str
    required_level:int
    allowed_classes:tuple[str,...]=()
    armor_type:str|None=None
    weapon_hands:int=1
    def __post_init__(self)->None:
        if self.slot_key not in ALL_GENERATED_SLOTS:raise ValueError("identity_slot_invalid")
        if not self.item_subtype or not self.display_name:raise ValueError("identity_text_invalid")
        if self.required_level<1:raise ValueError("required_level_invalid")
        if self.weapon_hands not in (1,2):raise ValueError("weapon_hands_invalid")
        if self.slot_key in JEWELRY_SLOTS and self.allowed_classes:raise ValueError("dropped_jewelry_must_be_universal")

@dataclass(frozen=True,slots=True)
class GeneratedEquipment:
    source:EquipmentGenerationSource
    item_level:int
    identity:EquipmentIdentity
    stats:Mapping[str,float]
    rarity:str
    def __post_init__(self)->None:
        if self.item_level!=self.identity.required_level:raise ValueError("level_semantic_mismatch")
        clean={str(k):float(v) for k,v in self.stats.items() if float(v)!=0.0}
        object.__setattr__(self,"stats",MappingProxyType(clean))
    @property
    def required_level(self)->int:
        """Expose the persisted generation level using the equip-facing V1 name."""
        return self.item_level
