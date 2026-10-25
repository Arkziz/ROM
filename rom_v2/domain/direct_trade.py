"""Pure Direct Trade state, offers and policy DTOs."""
from __future__ import annotations
from dataclasses import dataclass,replace
from enum import StrEnum
class TradeStatus(StrEnum):
 EDITING="editing";COMPLETED="completed";CANCELLED="cancelled";EXPIRED="expired"
TERMINAL_STATUSES=frozenset({TradeStatus.COMPLETED,TradeStatus.CANCELLED,TradeStatus.EXPIRED})
@dataclass(frozen=True,slots=True)
class TradeItemSnapshot:
 inventory_id:int;item_id:int;quantity:int;tradeable:bool=True;equipped:bool=False;auction_reserved:bool=False;bound_kind:str|None=None;item_key:str|None=None
 def __post_init__(self):
  if min(self.inventory_id,self.item_id,self.quantity)<1:raise ValueError("invalid_item_snapshot")
@dataclass(frozen=True,slots=True)
class TradeOffer:
 owner_user_id:int;items:tuple[TradeItemSnapshot,...]=();gold:int=0
 def __post_init__(self):
  if self.owner_user_id<1 or self.gold<0:raise ValueError("invalid_offer")
@dataclass(frozen=True,slots=True)
class DirectTrade:
 trade_id:int;initiator_id:int;recipient_id:int;location_id:str;revision:int=0;status:TradeStatus=TradeStatus.EDITING;initiator_offer:TradeOffer|None=None;recipient_offer:TradeOffer|None=None;initiator_ready:bool=False;recipient_ready:bool=False;initiator_confirmed:bool=False;recipient_confirmed:bool=False
 def __post_init__(self):
  if min(self.trade_id,self.initiator_id,self.recipient_id)<1 or self.initiator_id==self.recipient_id:raise ValueError("invalid_trade_identity")
  if not self.location_id.strip() or self.revision<0:raise ValueError("invalid_trade_state")
 def is_participant(self,user_id):return user_id in {self.initiator_id,self.recipient_id}
 def offer_for(self,user_id):return self.initiator_offer if user_id==self.initiator_id else self.recipient_offer if user_id==self.recipient_id else None
 def invalidate_confirmations(self):return replace(self,revision=self.revision+1,initiator_ready=False,recipient_ready=False,initiator_confirmed=False,recipient_confirmed=False)
@dataclass(frozen=True,slots=True)
class TradeResult:
 success:bool;reason:str|None=None;trade:DirectTrade|None=None;changed:bool=False;settlement_required:bool=False
BLOCKED_ITEM_KEYS=frozenset({"firius_token","rune_of_success","perfect_extractor","sphere_of_new_path"})
BLOCKED_BOUND_KINDS=frozenset({"quest","dev","premium"})
def item_policy(snapshot):
 if snapshot.equipped:return "equipped"
 if snapshot.auction_reserved:return "auction_reserved"
 if not snapshot.tradeable:return "not_tradeable"
 if snapshot.item_key in BLOCKED_ITEM_KEYS:return "blocked_item"
 if snapshot.bound_kind in BLOCKED_BOUND_KINDS:return "bound_item"
 return None
