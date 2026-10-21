"""Pure, typed and deterministic item presentation DTOs.

This module contains no persistence, pricing, chance, damage or mutation logic.
Callers provide already-resolved domain values; Telegram and tests consume the same
stable model instead of rebuilding item descriptions from presentation text.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from typing import Iterable,Mapping

PRIMARY_STAT_ORDER=("str","dex","int","wis","sta")
DEFENSE_ORDER=("pdef","mdef")
DAMAGE_ORDER=("physical_min","physical_max","magical_min","magical_max")

@dataclass(frozen=True,slots=True)
class RunePresentation:
    """Resolved rune information bound to a socket, without business behavior."""
    socket_index:int
    rune_id:int|None=None
    name:str=""
    stat_key:str=""
    value:int|float|None=None

@dataclass(frozen=True,slots=True)
class ItemPresentationInput:
    """Resolved source values needed to build description and comparison models."""
    item_id:int
    inventory_id:int|None
    name:str
    category:str=""
    slot_key:str=""
    item_subtype:str=""
    armor_type:str=""
    weapon_hands:int=1
    rarity:str="common"
    item_level:int=1
    required_level:int=1
    durability:int|None=None
    refine_level:int=0
    primary_stats:Mapping[str,int|float]=field(default_factory=dict)
    defenses:Mapping[str,int|float]=field(default_factory=dict)
    damage:Mapping[str,int|float]=field(default_factory=dict)
    runes:tuple[RunePresentation,...]=()

    def __post_init__(self)->None:
        if self.item_id<=0:raise ValueError("invalid_item_id")
        if self.inventory_id is not None and self.inventory_id<=0:raise ValueError("invalid_inventory_id")
        if not self.name:raise ValueError("missing_name")
        if self.weapon_hands not in (1,2):raise ValueError("invalid_weapon_hands")
        if self.item_level<1 or self.required_level<1:raise ValueError("invalid_level")
        if self.durability is not None and not 0<=self.durability<=100:raise ValueError("invalid_durability")
        if self.refine_level<0:raise ValueError("invalid_refine_level")

@dataclass(frozen=True,slots=True)
class PresentationField:
    """Stable machine key and resolved value; label is optional presentation metadata."""
    key:str
    value:str
    label:str=""

@dataclass(frozen=True,slots=True)
class ItemDescriptionDTO:
    item_id:int
    inventory_id:int|None
    display_name:str
    fields:tuple[PresentationField,...]
    runes:tuple[RunePresentation,...]

@dataclass(frozen=True,slots=True)
class ComparisonRow:
    key:str
    selected:str
    equipped:str
    relation:int

@dataclass(frozen=True,slots=True)
class ItemComparisonDTO:
    selected_inventory_id:int
    equipped_inventory_id:int
    rows:tuple[ComparisonRow,...]

def _value(value:int|float)->str:
    """Format resolved numeric values deterministically without locale dependency."""
    return str(int(value)) if isinstance(value,float) and value.is_integer() else str(value)

def _ordered_numeric(mapping:Mapping[str,int|float],order:Iterable[str])->tuple[PresentationField,...]:
    rows=[]
    for key in order:
        value=mapping.get(key)
        if value is not None and value!=0:rows.append(PresentationField(key,_value(value)))
    return tuple(rows)

def build_display_name(item:ItemPresentationInput)->str:
    """Build a stable display name without ever using it as technical identity."""
    suffix=f" +{item.refine_level}" if item.refine_level>0 else ""
    return f"{item.name}{suffix}"

def build_item_description(item:ItemPresentationInput)->ItemDescriptionDTO:
    """Create the single deterministic description model consumed by UI and tests."""
    fields=[PresentationField("category",item.category),PresentationField("slot_key",item.slot_key)]
    for key,value in (("item_subtype",item.item_subtype),("armor_type",item.armor_type),("rarity",item.rarity)):
        if value:fields.append(PresentationField(key,value))
    fields.extend((PresentationField("item_level",str(item.item_level)),PresentationField("required_level",str(item.required_level))))
    if item.durability is not None:fields.append(PresentationField("durability",str(item.durability)))
    fields.append(PresentationField("refine_level",str(item.refine_level)))
    fields.extend(_ordered_numeric(item.primary_stats,PRIMARY_STAT_ORDER))
    fields.extend(_ordered_numeric(item.defenses,DEFENSE_ORDER))
    fields.extend(_ordered_numeric(item.damage,DAMAGE_ORDER))
    runes=tuple(sorted(item.runes,key=lambda rune:rune.socket_index))
    return ItemDescriptionDTO(item.item_id,item.inventory_id,build_display_name(item),tuple(fields),runes)

def _number(value:str)->float|None:
    try:return float(value)
    except (TypeError,ValueError):return None

def compare_items(selected:ItemDescriptionDTO,equipped:ItemDescriptionDTO)->ItemComparisonDTO:
    """Compare exact owned instances by stable field keys, never by rendered text."""
    if selected.inventory_id is None or equipped.inventory_id is None:raise ValueError("comparison_requires_owned_instances")
    left={row.key:row.value for row in selected.fields};right={row.key:row.value for row in equipped.fields}
    ordered=[]
    for key in tuple(dict.fromkeys([*(row.key for row in selected.fields),*(row.key for row in equipped.fields)])):
        a,b=left.get(key,""),right.get(key,"");na,nb=_number(a),_number(b)
        relation=0 if na is None or nb is None or na==nb else 1 if na>nb else -1
        ordered.append(ComparisonRow(key,a,b,relation))
    return ItemComparisonDTO(selected.inventory_id,equipped.inventory_id,tuple(ordered))
