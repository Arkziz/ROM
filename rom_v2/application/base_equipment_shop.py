"""Pure API-ready Base Equipment Shop service for ROM V2."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

class ShopContractError(ValueError): pass
class ShopConflictError(ShopContractError): pass

@dataclass(frozen=True, slots=True)
class EquipmentSnapshot:
    template_key:str; slot_key:str; profile_key:str; class_key:str
    stats:tuple[tuple[str,int],...]; rarity_key:str; durability:int

@dataclass(frozen=True, slots=True)
class ShopOffer:
    offer_key:str; suboffer_key:str; class_key:str; slot_key:str; profile_key:str; price:int

@dataclass(frozen=True, slots=True)
class ShopPreview:
    preview_id:int; user_id:int; offer_key:str; suboffer_key:str; class_key:str
    item:EquipmentSnapshot; quoted_price:int; created_at:datetime

@dataclass(frozen=True, slots=True)
class ConfirmPurchase:
    operation_key:str; user_id:int; preview_id:int

@dataclass(frozen=True, slots=True)
class PurchaseReceipt:
    operation_key:str; user_id:int; preview_id:int; permanent_item_id:int
    price:int; balance_after:int; inventory_entry_id:int

@dataclass(frozen=True, slots=True)
class PurchaseResult:
    receipt:PurchaseReceipt; replayed:bool

class ShopRepositoryPort(Protocol):
    def get_preview(self,preview_id:int)->ShopPreview|None: ...
    def get_receipt(self,operation_key:str)->PurchaseReceipt|None: ...
    def save_receipt(self,receipt:PurchaseReceipt)->None: ...
    def invalidate_preview(self,preview_id:int)->None: ...
class ShopWalletPort(Protocol):
    def get_balance(self,user_id:int)->int: ...
    def debit(self,user_id:int,amount:int)->int: ...
class ShopInventoryPort(Protocol):
    def has_capacity(self,user_id:int)->bool: ...
    def insert(self,user_id:int,permanent_item_id:int,item:EquipmentSnapshot)->int: ...
class ShopItemAllocatorPort(Protocol):
    def promote(self,preview_id:int,item:EquipmentSnapshot)->int: ...
class ShopUnitOfWorkPort(Protocol):
    shop:ShopRepositoryPort; wallet:ShopWalletPort; inventory:ShopInventoryPort; allocator:ShopItemAllocatorPort
    def commit(self)->None: ...
    def rollback(self)->None: ...

class BaseEquipmentShopService:
    """Canonical owner for class-aware preview confirmation and atomic purchase."""
    def confirm(self,command:ConfirmPurchase,uow:ShopUnitOfWorkPort)->PurchaseResult:
        if not command.operation_key.strip():raise ShopContractError("operation_key_required")
        if command.user_id<=0 or command.preview_id<=0:raise ShopContractError("invalid_identity")
        try:
            existing=uow.shop.get_receipt(command.operation_key)
            if existing is not None:
                if existing.user_id!=command.user_id or existing.preview_id!=command.preview_id:raise ShopConflictError("operation_key_payload_conflict")
                return PurchaseResult(existing,True)
            preview=uow.shop.get_preview(command.preview_id)
            if preview is None:raise ShopContractError("preview_not_found_or_expired")
            if preview.user_id!=command.user_id:raise ShopContractError("preview_owner_mismatch")
            if preview.quoted_price<=0:raise ShopContractError("invalid_quoted_price")
            if not uow.inventory.has_capacity(command.user_id):raise ShopContractError("inventory_full")
            if uow.wallet.get_balance(command.user_id)<preview.quoted_price:raise ShopContractError("insufficient_gold")
            permanent_id=uow.allocator.promote(preview.preview_id,preview.item)
            inventory_id=uow.inventory.insert(command.user_id,permanent_id,preview.item)
            balance_after=uow.wallet.debit(command.user_id,preview.quoted_price)
            receipt=PurchaseReceipt(command.operation_key,command.user_id,preview.preview_id,permanent_id,preview.quoted_price,balance_after,inventory_id)
            uow.shop.save_receipt(receipt);uow.shop.invalidate_preview(preview.preview_id);uow.commit()
            return PurchaseResult(receipt,False)
        except Exception:
            uow.rollback();raise
