"""Pure Auction lot, snapshot, price and result contracts."""
from __future__ import annotations
from dataclasses import dataclass,replace
from decimal import Decimal,ROUND_DOWN,InvalidOperation
from enum import StrEnum
PRICE_QUANT=Decimal("0.01");MIN_PRICE=Decimal("1.00");MAX_PRICE=Decimal("999999.00");MAX_ACTIVE_LOTS=20;ACTIVE_DAYS=7
class LotStatus(StrEnum):
 ACTIVE="active";SOLD_UNCLAIMED="sold_unclaimed";SOLD_CLAIMED="sold_claimed";EXPIRED_UNCLAIMED="expired_unclaimed";EXPIRED_CLAIMED="expired_claimed";CANCELLED="cancelled"
TERMINAL=frozenset({LotStatus.SOLD_CLAIMED,LotStatus.EXPIRED_CLAIMED,LotStatus.CANCELLED})
@dataclass(frozen=True,slots=True)
class AuctionSnapshot:
 inventory_id:int;item_id:int;quantity:int;category:str;permanent_id:int|None=None;durability:int|None=None;refine_level:int=0;runes:tuple[str,...]=()
 def __post_init__(self):
  if min(self.inventory_id,self.item_id,self.quantity)<1 or not self.category.strip() or self.refine_level<0:raise ValueError("invalid_snapshot")
@dataclass(frozen=True,slots=True)
class AuctionLot:
 lot_id:int;seller_user_id:int;snapshot:AuctionSnapshot;price:Decimal;status:LotStatus=LotStatus.ACTIVE;buyer_user_id:int|None=None;expires_at:int=0
 def __post_init__(self):
  if min(self.lot_id,self.seller_user_id)<1:raise ValueError("invalid_lot_identity")
  object.__setattr__(self,"price",normalize_price(self.price))
@dataclass(frozen=True,slots=True)
class AuctionResult:
 success:bool;reason:str|None=None;lot:AuctionLot|None=None;changed:bool=False;transfer_required:bool=False
@dataclass(frozen=True,slots=True)
class AuctionPage:
 items:tuple[AuctionLot,...];total:int;limit:int;offset:int
def normalize_price(value):
 try:price=Decimal(str(value)).quantize(PRICE_QUANT,rounding=ROUND_DOWN)
 except (InvalidOperation,ValueError):raise ValueError("invalid_price")
 if price<MIN_PRICE or price>MAX_PRICE:raise ValueError("price_out_of_range")
 return price
def normalize_category(value):
 category=str(value or "").strip().lower()
 if not category:raise ValueError("invalid_category")
 return category
