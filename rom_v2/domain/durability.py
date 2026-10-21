"""Canonical durability value objects and V1 repair policy.

This module owns formula-only behavior. Persistence and payment remain atomic gateway
responsibilities so callers cannot partially debit gold or partially repair equipment.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

MIN_DURABILITY = 0
MAX_DURABILITY = 100
DEATH_DURABILITY_LOSS = 5
REPAIR_RATE = Decimal("0.05")

class DurabilityError(ValueError):
    """Raised when a durability command violates the canonical contract."""

class RepairFailure(str, Enum):
    NOT_FOUND="NOT_FOUND"
    NOT_OWNED="NOT_OWNED"
    NOT_EQUIPPED="NOT_EQUIPPED"
    RESERVED="RESERVED"
    ALREADY_FULL="ALREADY_FULL"
    INSUFFICIENT_GOLD="INSUFFICIENT_GOLD"
    PERSISTENCE_FAILURE="PERSISTENCE_FAILURE"

RARITY_REPAIR_MULTIPLIERS={
    "common":Decimal("1.0"),
    "uncommon":Decimal("2.5"),
    "rare":Decimal("7.0"),
    "epic":Decimal("18.0"),
}

def clamp_durability(value:int)->int:
    """Clamp persistent durability to V1's inclusive 0..100 range."""
    return max(MIN_DURABILITY,min(MAX_DURABILITY,int(value)))

def rarity_repair_multiplier(rarity:str)->Decimal:
    """Return the exact V1 rarity multiplier; unknown rarity fails closed."""
    key=str(rarity).strip().lower()
    try:return RARITY_REPAIR_MULTIPLIERS[key]
    except KeyError as exc:raise DurabilityError(f"unsupported_rarity:{key}") from exc

def calculate_repair_cost(durability:int,rarity:str)->int:
    """Calculate V1 repair cost: missing durability x rarity multiplier x 0.05.

    Gold is indivisible. ROUND_HALF_UP preserves the V1 integer-facing payment
    boundary and prevents a fractional debit from leaking into persistence.
    """
    current=clamp_durability(durability)
    if current>=MAX_DURABILITY:return 0
    raw=Decimal(MAX_DURABILITY-current)*rarity_repair_multiplier(rarity)*REPAIR_RATE
    return max(1,int(raw.quantize(Decimal("1"),rounding=ROUND_HALF_UP)))

def damage_durability(durability:int,amount:int)->int:
    """Apply non-negative damage while preserving the canonical clamp."""
    if int(amount)<0:raise DurabilityError("negative_damage")
    return clamp_durability(clamp_durability(durability)-int(amount))

def damage_on_death(durability:int)->int:
    """Apply the exact V1 death penalty of five durability to equipped items."""
    return damage_durability(durability,DEATH_DURABILITY_LOSS)

def contributes_stats(durability:int)->bool:
    """Base stats, runes and enhancement contribute only above zero durability."""
    return clamp_durability(durability)>MIN_DURABILITY

@dataclass(frozen=True,slots=True)
class EquippedDurability:
    inventory_id:int
    durability:int
    rarity:str
    reserved:bool=False
    def __post_init__(self)->None:
        if self.inventory_id<=0:raise DurabilityError("invalid_inventory_id")
        object.__setattr__(self,"durability",clamp_durability(self.durability))
        rarity_repair_multiplier(self.rarity)

@dataclass(frozen=True,slots=True)
class RepairQuote:
    inventory_id:int
    durability_before:int
    durability_after:int
    cost:int

@dataclass(frozen=True,slots=True)
class RepairResult:
    success:bool
    total_cost:int=0
    repaired_inventory_ids:tuple[int,...]=()
    failure:RepairFailure|None=None
