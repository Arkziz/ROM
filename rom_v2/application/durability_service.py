"""Atomic application service for V1-parity durability and repair."""
from __future__ import annotations
from typing import Protocol,Sequence
from rom_v2.domain.durability import (
    DEATH_DURABILITY_LOSS,MAX_DURABILITY,EquippedDurability,RepairFailure,
    RepairQuote,RepairResult,calculate_repair_cost,damage_durability,
)

class DurabilityGateway(Protocol):
    """Persistence boundary; each mutation method must be one atomic transaction."""
    def list_equipped(self,user_id:int)->Sequence[EquippedDurability]:...
    def repair_atomically(self,user_id:int,quotes:Sequence[RepairQuote])->RepairResult:...
    def damage_equipped_atomically(self,user_id:int,amount:int)->tuple[int,...]:...

class DurabilityService:
    """Single canonical V2 orchestrator for equipped-item durability."""
    def __init__(self,gateway:DurabilityGateway)->None:self._gateway=gateway

    def _equipped(self,user_id:int)->tuple[EquippedDurability,...]:
        if int(user_id)<=0:raise ValueError("invalid_user_id")
        rows=tuple(self._gateway.list_equipped(int(user_id)))
        ids=[row.inventory_id for row in rows]
        if len(ids)!=len(set(ids)):raise ValueError("duplicate_inventory_id")
        return rows

    def quote_one(self,user_id:int,inventory_id:int)->RepairQuote|RepairResult:
        """Quote an exact owned equipped instance and fail closed for reservations."""
        row=next((x for x in self._equipped(user_id) if x.inventory_id==int(inventory_id)),None)
        if row is None:return RepairResult(False,failure=RepairFailure.NOT_EQUIPPED)
        if row.reserved:return RepairResult(False,failure=RepairFailure.RESERVED)
        cost=calculate_repair_cost(row.durability,row.rarity)
        if cost==0:return RepairResult(False,failure=RepairFailure.ALREADY_FULL)
        return RepairQuote(row.inventory_id,row.durability,MAX_DURABILITY,cost)

    def repair_one(self,user_id:int,inventory_id:int)->RepairResult:
        quote=self.quote_one(user_id,inventory_id)
        if isinstance(quote,RepairResult):return quote
        return self._gateway.repair_atomically(int(user_id),(quote,))

    def quote_all(self,user_id:int)->tuple[RepairQuote,...]|RepairResult:
        rows=self._equipped(user_id)
        if any(row.reserved for row in rows):
            return RepairResult(False,failure=RepairFailure.RESERVED)
        quotes=tuple(RepairQuote(row.inventory_id,row.durability,MAX_DURABILITY,calculate_repair_cost(row.durability,row.rarity)) for row in rows if row.durability<MAX_DURABILITY)
        if not quotes:return RepairResult(False,failure=RepairFailure.ALREADY_FULL)
        return quotes

    def repair_all(self,user_id:int)->RepairResult:
        quotes=self.quote_all(user_id)
        if isinstance(quotes,RepairResult):return quotes
        return self._gateway.repair_atomically(int(user_id),quotes)

    def damage_equipped(self,user_id:int,amount:int)->tuple[int,...]:
        if int(amount)<0:raise ValueError("negative_damage")
        if int(amount)==0:return ()
        return self._gateway.damage_equipped_atomically(int(user_id),int(amount))

    def damage_equipped_on_death(self,user_id:int)->tuple[int,...]:
        return self.damage_equipped(user_id,DEATH_DURABILITY_LOSS)
