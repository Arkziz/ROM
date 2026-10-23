"""Pure API-ready Premium Shop service for ROM V2."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

class PremiumShopContractError(ValueError): pass
class PremiumShopConflictError(PremiumShopContractError): pass

@dataclass(frozen=True, slots=True)
class PremiumPlan:
    plan_key:str
    duration_days:int
    price_crystals:int

PREMIUM_PLANS={
    "premium_15d":PremiumPlan("premium_15d",15,100),
    "premium_30d":PremiumPlan("premium_30d",30,180),
}

@dataclass(frozen=True, slots=True)
class PremiumPurchaseCommand:
    operation_key:str
    user_id:int
    plan_key:str
    quoted_price_crystals:int

@dataclass(frozen=True, slots=True)
class PremiumPurchaseReceipt:
    operation_key:str
    user_id:int
    plan_key:str
    price_crystals:int
    previous_expiry:datetime|None
    base_expiry:datetime
    new_expiry:datetime
    crystal_balance_after:int

@dataclass(frozen=True, slots=True)
class PremiumPurchaseResult:
    receipt:PremiumPurchaseReceipt
    replayed:bool

class PremiumAccountPort(Protocol):
    def get_expiry(self,user_id:int)->datetime|None: ...
    def set_expiry(self,user_id:int,expiry:datetime)->None: ...
class PremiumCrystalWalletPort(Protocol):
    def get_balance(self,user_id:int)->int: ...
    def debit(self,user_id:int,amount:int)->int: ...
class PremiumReceiptPort(Protocol):
    def get_receipt(self,operation_key:str)->PremiumPurchaseReceipt|None: ...
    def save_receipt(self,receipt:PremiumPurchaseReceipt)->None: ...
class PremiumClockPort(Protocol):
    def now_utc(self)->datetime: ...
class PremiumShopUnitOfWorkPort(Protocol):
    account:PremiumAccountPort
    wallet:PremiumCrystalWalletPort
    receipts:PremiumReceiptPort
    clock:PremiumClockPort
    def commit(self)->None: ...
    def rollback(self)->None: ...

class PremiumShopService:
    """Canonical owner for atomic account-level Premium activation and extension."""
    def purchase(self,command:PremiumPurchaseCommand,uow:PremiumShopUnitOfWorkPort)->PremiumPurchaseResult:
        self._validate_command(command)
        try:
            existing=uow.receipts.get_receipt(command.operation_key)
            if existing is not None:
                if not self._same_payload(existing,command):raise PremiumShopConflictError("operation_key_payload_conflict")
                return PremiumPurchaseResult(existing,True)
            plan=PREMIUM_PLANS.get(command.plan_key)
            if plan is None:raise PremiumShopContractError("unknown_premium_plan")
            if command.quoted_price_crystals!=plan.price_crystals:raise PremiumShopContractError("stale_plan_price")
            now=self._utc(uow.clock.now_utc(),"clock_must_return_aware_utc")
            previous=uow.account.get_expiry(command.user_id)
            if previous is not None:previous=self._utc(previous,"stored_expiry_must_be_aware_utc")
            base=previous if previous is not None and previous>now else now
            new_expiry=base+timedelta(days=plan.duration_days)
            if uow.wallet.get_balance(command.user_id)<plan.price_crystals:raise PremiumShopContractError("insufficient_crystals")
            balance_after=uow.wallet.debit(command.user_id,plan.price_crystals)
            uow.account.set_expiry(command.user_id,new_expiry)
            receipt=PremiumPurchaseReceipt(command.operation_key,command.user_id,plan.plan_key,plan.price_crystals,previous,base,new_expiry,balance_after)
            uow.receipts.save_receipt(receipt);uow.commit()
            return PremiumPurchaseResult(receipt,False)
        except Exception:
            uow.rollback();raise
    @staticmethod
    def _validate_command(command:PremiumPurchaseCommand)->None:
        if not command.operation_key.strip():raise PremiumShopContractError("operation_key_required")
        if command.user_id<=0:raise PremiumShopContractError("user_id_must_be_positive")
        if not command.plan_key.strip():raise PremiumShopContractError("plan_key_required")
        if not isinstance(command.quoted_price_crystals,int) or isinstance(command.quoted_price_crystals,bool) or command.quoted_price_crystals<=0:raise PremiumShopContractError("invalid_quoted_price")
    @staticmethod
    def _utc(value:datetime,reason:str)->datetime:
        if value.tzinfo is None or value.utcoffset() is None:raise PremiumShopContractError(reason)
        return value.astimezone(timezone.utc)
    @staticmethod
    def _same_payload(receipt:PremiumPurchaseReceipt,command:PremiumPurchaseCommand)->bool:
        return receipt.user_id==command.user_id and receipt.plan_key==command.plan_key and receipt.price_crystals==command.quoted_price_crystals
