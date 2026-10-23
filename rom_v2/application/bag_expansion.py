"""Pure API-ready Bag Expansion service for ROM V2."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

class BagExpansionContractError(ValueError): pass
class BagExpansionConflictError(BagExpansionContractError): pass

@dataclass(frozen=True, slots=True)
class BagExpansionDefinition:
    expansion_key:str
    from_capacity:int
    to_capacity:int
    price_crystals:int

EXPANSIONS={
    "bag_60_to_80":BagExpansionDefinition("bag_60_to_80",60,80,75),
    "bag_80_to_100":BagExpansionDefinition("bag_80_to_100",80,100,150),
}
MAXIMUM_CAPACITY=100

@dataclass(frozen=True, slots=True)
class BagExpansionCommand:
    operation_key:str
    user_id:int
    expansion_key:str
    quoted_from_capacity:int
    quoted_to_capacity:int
    quoted_price_crystals:int

@dataclass(frozen=True, slots=True)
class BagExpansionReceipt:
    operation_key:str
    user_id:int
    expansion_key:str
    previous_capacity:int
    target_capacity:int
    price_crystals:int
    crystal_balance_after:int

@dataclass(frozen=True, slots=True)
class BagExpansionResult:
    receipt:BagExpansionReceipt
    replayed:bool

class BagCapacityPort(Protocol):
    def get_capacity(self,user_id:int)->int: ...
    def set_capacity(self,user_id:int,capacity:int)->None: ...
class BagExpansionCrystalWalletPort(Protocol):
    def get_balance(self,user_id:int)->int: ...
    def debit(self,user_id:int,amount:int)->int: ...
class BagExpansionReceiptPort(Protocol):
    def get_receipt(self,operation_key:str)->BagExpansionReceipt|None: ...
    def save_receipt(self,receipt:BagExpansionReceipt)->None: ...
class BagExpansionUnitOfWorkPort(Protocol):
    capacity:BagCapacityPort
    wallet:BagExpansionCrystalWalletPort
    receipts:BagExpansionReceiptPort
    def commit(self)->None: ...
    def rollback(self)->None: ...

class BagExpansionService:
    """Canonical owner for sequential account-level bag expansion purchases."""
    def purchase(self,command:BagExpansionCommand,uow:BagExpansionUnitOfWorkPort)->BagExpansionResult:
        self._validate_command(command)
        try:
            existing=uow.receipts.get_receipt(command.operation_key)
            if existing is not None:
                if not self._same_payload(existing,command):raise BagExpansionConflictError("operation_key_payload_conflict")
                return BagExpansionResult(existing,True)
            definition=EXPANSIONS.get(command.expansion_key)
            if definition is None:raise BagExpansionContractError("unknown_expansion")
            current=uow.capacity.get_capacity(command.user_id)
            if current==MAXIMUM_CAPACITY:raise BagExpansionContractError("maximum_capacity")
            if current not in (60,80):raise BagExpansionContractError("invalid_current_capacity")
            if current!=command.quoted_from_capacity:raise BagExpansionContractError("stale_capacity")
            if definition.from_capacity!=current or definition.to_capacity!=command.quoted_to_capacity:raise BagExpansionContractError("invalid_sequential_transition")
            if definition.price_crystals!=command.quoted_price_crystals:raise BagExpansionContractError("stale_price")
            if uow.wallet.get_balance(command.user_id)<definition.price_crystals:raise BagExpansionContractError("insufficient_crystals")
            balance_after=uow.wallet.debit(command.user_id,definition.price_crystals)
            uow.capacity.set_capacity(command.user_id,definition.to_capacity)
            receipt=BagExpansionReceipt(command.operation_key,command.user_id,definition.expansion_key,current,definition.to_capacity,definition.price_crystals,balance_after)
            uow.receipts.save_receipt(receipt);uow.commit()
            return BagExpansionResult(receipt,False)
        except Exception:
            uow.rollback();raise
    @staticmethod
    def _validate_command(command:BagExpansionCommand)->None:
        if not command.operation_key.strip():raise BagExpansionContractError("operation_key_required")
        if command.user_id<=0:raise BagExpansionContractError("user_id_must_be_positive")
        if not command.expansion_key.strip():raise BagExpansionContractError("expansion_key_required")
        for value,reason in ((command.quoted_from_capacity,"invalid_from_capacity"),(command.quoted_to_capacity,"invalid_to_capacity"),(command.quoted_price_crystals,"invalid_quoted_price")):
            if not isinstance(value,int) or isinstance(value,bool) or value<=0:raise BagExpansionContractError(reason)
    @staticmethod
    def _same_payload(receipt:BagExpansionReceipt,command:BagExpansionCommand)->bool:
        return receipt.user_id==command.user_id and receipt.expansion_key==command.expansion_key and receipt.previous_capacity==command.quoted_from_capacity and receipt.target_capacity==command.quoted_to_capacity and receipt.price_crystals==command.quoted_price_crystals
