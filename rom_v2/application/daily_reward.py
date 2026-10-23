"""Pure API-ready Daily Reward service for ROM V2.

The only authorized reward is three small HP potions plus three Phirius Tokens.
The superseded five-token value is intentionally absent from this module.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

REWARD_KEY="daily_reward_3hp_3firius"
SMALL_HP_POTION_KEY="small_hp_potion"
SMALL_HP_POTION_QUANTITY=3
PHIRIUS_TOKEN_KEY="phirius_token"
PHIRIUS_TOKEN_QUANTITY=3

class DailyRewardContractError(ValueError): pass
class DailyRewardConflictError(DailyRewardContractError): pass

@dataclass(frozen=True, slots=True)
class DailyRewardDefinition:
    reward_key:str=REWARD_KEY
    small_hp_potion_key:str=SMALL_HP_POTION_KEY
    small_hp_potion_quantity:int=SMALL_HP_POTION_QUANTITY
    phirius_token_key:str=PHIRIUS_TOKEN_KEY
    phirius_token_quantity:int=PHIRIUS_TOKEN_QUANTITY

@dataclass(frozen=True, slots=True)
class DailyRewardClaimCommand:
    operation_key:str
    user_id:int
    period_key:str
    reward_key:str=REWARD_KEY

@dataclass(frozen=True, slots=True)
class DailyRewardStackPlan:
    item_key:str
    quantity_before:int
    quantity_delta:int
    quantity_after:int

@dataclass(frozen=True, slots=True)
class DailyRewardReceipt:
    operation_key:str
    user_id:int
    period_key:str
    reward_key:str
    small_hp_potions_granted:int
    phirius_tokens_granted:int
    small_hp_quantity_after:int
    phirius_token_quantity_after:int

@dataclass(frozen=True, slots=True)
class DailyRewardResult:
    receipt:DailyRewardReceipt
    replayed:bool

class DailyQuestStatePort(Protocol):
    def exists(self,user_id:int,period_key:str)->bool: ...
    def is_complete(self,user_id:int,period_key:str)->bool: ...
    def is_claimed(self,user_id:int,period_key:str)->bool: ...
    def mark_claimed(self,user_id:int,period_key:str)->None: ...
class DailyPeriodPort(Protocol):
    def current_period_key(self)->str: ...
class DailyRewardInventoryPort(Protocol):
    def quantity(self,user_id:int,item_key:str)->int: ...
    def build_add_plan(self,user_id:int,item_key:str,quantity:int)->DailyRewardStackPlan: ...
    def validate_capacity(self,user_id:int,plan:DailyRewardStackPlan)->None: ...
    def apply_plan(self,user_id:int,plan:DailyRewardStackPlan)->None: ...
class DailyRewardTokenWalletPort(Protocol):
    def credit(self,user_id:int,token_key:str,quantity:int)->int: ...
class DailyRewardReceiptPort(Protocol):
    def get_receipt(self,operation_key:str)->DailyRewardReceipt|None: ...
    def get_period_receipt(self,user_id:int,period_key:str)->DailyRewardReceipt|None: ...
    def save_receipt(self,receipt:DailyRewardReceipt)->None: ...
class DailyRewardUnitOfWorkPort(Protocol):
    quest:DailyQuestStatePort
    period:DailyPeriodPort
    inventory:DailyRewardInventoryPort
    tokens:DailyRewardTokenWalletPort
    receipts:DailyRewardReceiptPort
    def commit(self)->None: ...
    def rollback(self)->None: ...

class DailyRewardService:
    """Canonical owner for exact-once atomic Daily Reward settlement."""
    reward=DailyRewardDefinition()
    def claim(self,command:DailyRewardClaimCommand,uow:DailyRewardUnitOfWorkPort)->DailyRewardResult:
        self._validate_command(command)
        try:
            replay=uow.receipts.get_receipt(command.operation_key)
            if replay is not None:
                if not self._same_payload(replay,command):raise DailyRewardConflictError("operation_key_payload_conflict")
                return DailyRewardResult(replay,True)
            current_period=uow.period.current_period_key()
            if not current_period.strip():raise DailyRewardContractError("invalid_current_period")
            if command.period_key!=current_period:raise DailyRewardContractError("stale_period")
            if not uow.quest.exists(command.user_id,command.period_key):raise DailyRewardContractError("daily_quest_not_found")
            if not uow.quest.is_complete(command.user_id,command.period_key):raise DailyRewardContractError("daily_quest_incomplete")
            prior=uow.receipts.get_period_receipt(command.user_id,command.period_key)
            if prior is not None or uow.quest.is_claimed(command.user_id,command.period_key):raise DailyRewardContractError("already_claimed")
            before=uow.inventory.quantity(command.user_id,SMALL_HP_POTION_KEY)
            plan=uow.inventory.build_add_plan(command.user_id,SMALL_HP_POTION_KEY,SMALL_HP_POTION_QUANTITY)
            self._validate_plan(plan,before)
            uow.inventory.validate_capacity(command.user_id,plan)
            uow.inventory.apply_plan(command.user_id,plan)
            token_after=uow.tokens.credit(command.user_id,PHIRIUS_TOKEN_KEY,PHIRIUS_TOKEN_QUANTITY)
            uow.quest.mark_claimed(command.user_id,command.period_key)
            receipt=DailyRewardReceipt(command.operation_key,command.user_id,command.period_key,REWARD_KEY,SMALL_HP_POTION_QUANTITY,PHIRIUS_TOKEN_QUANTITY,plan.quantity_after,token_after)
            uow.receipts.save_receipt(receipt);uow.commit()
            return DailyRewardResult(receipt,False)
        except Exception:
            uow.rollback();raise
    @staticmethod
    def _validate_command(command:DailyRewardClaimCommand)->None:
        if not command.operation_key.strip():raise DailyRewardContractError("operation_key_required")
        if command.user_id<=0:raise DailyRewardContractError("user_id_must_be_positive")
        if not command.period_key.strip():raise DailyRewardContractError("period_key_required")
        if command.reward_key!=REWARD_KEY:raise DailyRewardContractError("invalid_reward_key")
    @staticmethod
    def _validate_plan(plan:DailyRewardStackPlan,before:int)->None:
        if plan.item_key!=SMALL_HP_POTION_KEY or plan.quantity_before!=before or plan.quantity_delta!=SMALL_HP_POTION_QUANTITY or plan.quantity_after!=before+SMALL_HP_POTION_QUANTITY:
            raise DailyRewardContractError("invalid_reward_stack_plan")
    @staticmethod
    def _same_payload(receipt:DailyRewardReceipt,command:DailyRewardClaimCommand)->bool:
        return receipt.user_id==command.user_id and receipt.period_key==command.period_key and receipt.reward_key==command.reward_key
