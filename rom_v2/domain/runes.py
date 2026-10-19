"""Canonical V2 rune lifecycle value objects and failure taxonomy."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

class RuneFailure(StrEnum):
    INVALID_IDENTITY="invalid_identity"
    NOT_OWNED="not_owned"
    RESERVED="reserved"
    NOT_EQUIPMENT="not_equipment"
    INCOMPATIBLE_CLASS="incompatible_class"
    INVALID_SOCKET="invalid_socket"
    SOCKET_OCCUPIED="socket_occupied"
    NO_EXTRACTOR="no_extractor"
    INSUFFICIENT_GOLD="insufficient_gold"
    RUNE_NOT_FOUND="rune_not_found"
    CONCURRENT_CHANGE="concurrent_change"

@dataclass(frozen=True, slots=True)
class RuneDefinition:
    """Immutable audited rune definition supplied by the canonical catalog."""
    item_id:int
    key:str
    stat_key:str
    level:int
    value:float
    allowed_classes:tuple[str,...]=()
    def __post_init__(self)->None:
        if self.item_id<=0 or not self.key or not self.stat_key or self.level<=0 or self.value<=0:
            raise ValueError(RuneFailure.INVALID_IDENTITY)

@dataclass(frozen=True, slots=True)
class RuneSocket:
    slot_index:int
    rune:RuneDefinition
    source_inventory_id:int
    def __post_init__(self)->None:
        if self.slot_index<0 or self.source_inventory_id<=0:
            raise ValueError(RuneFailure.INVALID_IDENTITY)

@dataclass(frozen=True, slots=True)
class RuneEquipmentState:
    """Exact owned equipment state; sockets are keyed by stable zero-based index."""
    inventory_id:int
    owner_user_id:int
    slot_key:str
    socket_capacity:int
    equipped:bool
    durability:int
    sockets:Mapping[int,RuneSocket]
    allowed_classes:tuple[str,...]=()
    def __post_init__(self)->None:
        if self.inventory_id<=0 or self.owner_user_id<=0 or not self.slot_key:
            raise ValueError(RuneFailure.INVALID_IDENTITY)
        if self.socket_capacity<0 or self.durability<0:
            raise ValueError(RuneFailure.INVALID_IDENTITY)
        normalized=dict(self.sockets)
        if any(i<0 or i>=self.socket_capacity or i!=s.slot_index for i,s in normalized.items()):
            raise ValueError(RuneFailure.INVALID_SOCKET)
        # Store a private plain-dict snapshot: the frozen dataclass prevents rebinding,
        # while copy/pickle support is required for restart-shaped verification.
        object.__setattr__(self,"sockets",normalized)

@dataclass(frozen=True, slots=True)
class RuneMutationResult:
    success:bool
    code:str
    equipment:RuneEquipmentState|None=None
    returned_rune_item_id:int|None=None
    consumed_extractor_item_id:int|None=None
    gold_spent:int=0

@dataclass(frozen=True, slots=True)
class RuneStatContribution:
    stat_key:str
    value:float
    rune_item_id:int
    equipment_inventory_id:int
    socket_index:int
