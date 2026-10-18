"""Audited V1-parity lifecycle for persistent current HP and MP."""
from __future__ import annotations
from dataclasses import dataclass

MANA_CLASSES=frozenset({"mage","priest"})

@dataclass(frozen=True, slots=True)
class ResourceState:
    """Persistent current resources plus calculated maximums."""
    current_hp:int
    max_hp:int
    current_mp:int
    max_mp:int
    def __post_init__(self)->None:
        if self.max_hp<1: raise ValueError("max_hp_invalid")
        if not 0<=self.current_hp<=self.max_hp: raise ValueError("current_hp_out_of_range")
        if self.max_mp<0: raise ValueError("max_mp_invalid")
        if not 0<=self.current_mp<=self.max_mp: raise ValueError("current_mp_out_of_range")

def initialize_resources(class_key:str,max_hp:int,max_mp:int)->ResourceState:
    """Create a full-health state; non-mana classes always have zero MP."""
    hp=max(1,int(max_hp))
    mana_class=str(class_key or "").strip().casefold() in MANA_CLASSES
    mp=max(0,int(max_mp)) if mana_class else 0
    return ResourceState(hp,hp,mp,mp)

def synchronize_maximums(state:ResourceState,class_key:str,new_max_hp:int,new_max_mp:int)->ResourceState:
    """Preserve current values on max increase and clamp on max decrease."""
    hp_max=max(1,int(new_max_hp))
    mana_class=str(class_key or "").strip().casefold() in MANA_CLASSES
    mp_max=max(0,int(new_max_mp)) if mana_class else 0
    return ResourceState(min(state.current_hp,hp_max),hp_max,min(state.current_mp,mp_max),mp_max)

def set_current_resources(state:ResourceState,*,current_hp:int|None=None,current_mp:int|None=None)->ResourceState:
    """Clamp explicit writes to the audited persistent resource bounds."""
    hp=state.current_hp if current_hp is None else max(0,min(int(current_hp),state.max_hp))
    mp=state.current_mp if current_mp is None else max(0,min(int(current_mp),state.max_mp))
    return ResourceState(hp,state.max_hp,mp,state.max_mp)

def restore_resources(state:ResourceState,*,hp_amount:int=0,mp_amount:int=0)->ResourceState:
    """Apply explicit restoration without overheal or MP overfill."""
    if hp_amount<0 or mp_amount<0: raise ValueError("resource_restore_amount_invalid")
    return ResourceState(min(state.max_hp,state.current_hp+int(hp_amount)),state.max_hp,min(state.max_mp,state.current_mp+int(mp_amount)),state.max_mp)

def apply_pve_defeat(state:ResourceState)->ResourceState:
    """Apply the audited PvE terminal rule: the character remains at one HP."""
    return ResourceState(1,state.max_hp,state.current_mp,state.max_mp)
