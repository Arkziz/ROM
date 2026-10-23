"""Pure API-ready Potion Trading service for ROM V2.

The service uses typed potion keys, immutable quoted prices, reservation-aware
sell validation, deterministic stack plans and one caller-owned transaction.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

class PotionTradingContractError(ValueError): pass
class PotionTradingConflictError(PotionTradingContractError): pass
class TradeDirection(str, Enum):
    BUY="buy"
    SELL="sell"

@dataclass(frozen=True, slots=True)
class PotionQuote:
    potion_key:str
    direction:TradeDirection
    unit_price:int

@dataclass(frozen=True, slots=True)
class PotionTradeCommand:
    operation_key:str
    user_id:int
    potion_key:str
    direction:TradeDirection
    quantity:int
    quoted_unit_price:int

@dataclass(frozen=True, slots=True)
class StackPlan:
    potion_key:str
    quantity_before:int
    quantity_delta:int
    quantity_after:int

@dataclass(frozen=True, slots=True)
class PotionTradeReceipt:
    operation_key:str
    user_id:int
    potion_key:str
    direction:TradeDirection
    quantity:int
    unit_price:int
    gold_delta:int
    balance_after:int
    quantity_after:int

@dataclass(frozen=True, slots=True)
class PotionTradeResult:
    receipt:PotionTradeReceipt
    replayed:bool

class PotionCatalogPort(Protocol):
    def get_unit_price(self,potion_key:str,direction:TradeDirection)->int|None: ...
class PotionInventoryPort(Protocol):
    def get_quantity(self,user_id:int,potion_key:str)->int: ...
    def get_reserved_quantity(self,user_id:int,potion_key:str)->int: ...
    def build_stack_plan(self,user_id:int,potion_key:str,delta:int)->StackPlan: ...
    def apply_stack_plan(self,user_id:int,plan:StackPlan)->None: ...
class PotionWalletPort(Protocol):
    def get_balance(self,user_id:int)->int: ...
    def debit(self,user_id:int,amount:int)->int: ...
    def credit(self,user_id:int,amount:int)->int: ...
class PotionReceiptPort(Protocol):
    def get_receipt(self,operation_key:str)->PotionTradeReceipt|None: ...
    def save_receipt(self,receipt:PotionTradeReceipt)->None: ...
class PotionTradingUnitOfWorkPort(Protocol):
    catalog:PotionCatalogPort
    inventory:PotionInventoryPort
    wallet:PotionWalletPort
    receipts:PotionReceiptPort
    def commit(self)->None: ...
    def rollback(self)->None: ...

class PotionTradingService:
    """Canonical V2 owner for atomic Alchemist potion buy and sell operations."""
    def execute(self,command:PotionTradeCommand,uow:PotionTradingUnitOfWorkPort)->PotionTradeResult:
        self._validate_command(command)
        try:
            existing=uow.receipts.get_receipt(command.operation_key)
            if existing is not None:
                if not self._same_payload(existing,command):
                    raise PotionTradingConflictError("operation_key_payload_conflict")
                return PotionTradeResult(existing,True)
            current_price=uow.catalog.get_unit_price(command.potion_key,command.direction)
            if current_price is None:raise PotionTradingContractError("potion_not_allowed")
            if current_price!=command.quoted_unit_price:raise PotionTradingContractError("stale_price")
            total=command.quantity*command.quoted_unit_price
            before=uow.inventory.get_quantity(command.user_id,command.potion_key)
            if before<0:raise PotionTradingContractError("invalid_inventory_quantity")
            if command.direction is TradeDirection.BUY:
                if uow.wallet.get_balance(command.user_id)<total:raise PotionTradingContractError("insufficient_gold")
                plan=uow.inventory.build_stack_plan(command.user_id,command.potion_key,command.quantity)
                self._validate_plan(plan,command,before)
                balance_after=uow.wallet.debit(command.user_id,total)
                gold_delta=-total
            else:
                reserved=uow.inventory.get_reserved_quantity(command.user_id,command.potion_key)
                if reserved<0 or reserved>before:raise PotionTradingContractError("invalid_reserved_quantity")
                if command.quantity>before-reserved:raise PotionTradingContractError("insufficient_available_quantity")
                plan=uow.inventory.build_stack_plan(command.user_id,command.potion_key,-command.quantity)
                self._validate_plan(plan,command,before)
                balance_after=uow.wallet.credit(command.user_id,total)
                gold_delta=total
            uow.inventory.apply_stack_plan(command.user_id,plan)
            receipt=PotionTradeReceipt(command.operation_key,command.user_id,command.potion_key,command.direction,command.quantity,command.quoted_unit_price,gold_delta,balance_after,plan.quantity_after)
            uow.receipts.save_receipt(receipt);uow.commit()
            return PotionTradeResult(receipt,False)
        except Exception:
            uow.rollback();raise
    @staticmethod
    def _validate_command(command:PotionTradeCommand)->None:
        if not command.operation_key.strip():raise PotionTradingContractError("operation_key_required")
        if command.user_id<=0:raise PotionTradingContractError("user_id_must_be_positive")
        if not command.potion_key.strip():raise PotionTradingContractError("potion_key_required")
        if not isinstance(command.direction,TradeDirection):raise PotionTradingContractError("invalid_direction")
        if not isinstance(command.quantity,int) or isinstance(command.quantity,bool):raise PotionTradingContractError("quantity_must_be_int")
        if command.quantity<=0:raise PotionTradingContractError("quantity_must_be_positive")
        if not isinstance(command.quoted_unit_price,int) or isinstance(command.quoted_unit_price,bool) or command.quoted_unit_price<=0:raise PotionTradingContractError("invalid_quoted_unit_price")
    @staticmethod
    def _validate_plan(plan:StackPlan,command:PotionTradeCommand,before:int)->None:
        expected_delta=command.quantity if command.direction is TradeDirection.BUY else -command.quantity
        if plan.potion_key!=command.potion_key or plan.quantity_before!=before or plan.quantity_delta!=expected_delta or plan.quantity_after!=before+expected_delta or plan.quantity_after<0:
            raise PotionTradingContractError("invalid_stack_plan")
    @staticmethod
    def _same_payload(receipt:PotionTradeReceipt,command:PotionTradeCommand)->bool:
        return receipt.user_id==command.user_id and receipt.potion_key==command.potion_key and receipt.direction is command.direction and receipt.quantity==command.quantity and receipt.unit_price==command.quoted_unit_price
