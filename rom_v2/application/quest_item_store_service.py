from __future__ import annotations
from dataclasses import replace
from rom_v2.domain.quest_item_store import V2QuestItemBalance,V2QuestItemBalanceKey,V2QuestItemCollection,V2QuestItemStoreResult,V2QuestItemTurnInPlan

class InMemoryV2QuestItemStoreUow:
    def __init__(self) -> None:
        self.balances: dict[V2QuestItemBalanceKey,V2QuestItemBalance] = {}
        self.events: set[tuple[int,int,str]] = set()
        self.completions: set[str] = set()
    def get(self,key:V2QuestItemBalanceKey)->V2QuestItemBalance:
        return self.balances.get(key,V2QuestItemBalance(key,0,0))
    def put(self,balance:V2QuestItemBalance)->None:
        if balance.quantity == 0:self.balances.pop(balance.key,None)
        else:self.balances[balance.key]=balance

class V2QuestItemStoreService:
    def __init__(self,uow:InMemoryV2QuestItemStoreUow):self.uow=uow
    def quantity(self,key:V2QuestItemBalanceKey)->int:return self.uow.get(key).quantity
    def total_quantity(self,user_id:int,item_key:str)->int:
        return sum(v.quantity for k,v in self.uow.balances.items() if k.user_id==user_id and k.item_key==item_key)
    def collect(self,collection:V2QuestItemCollection)->V2QuestItemStoreResult:
        identity=(collection.key.user_id,collection.key.quest_id,collection.event_id)
        if identity in self.uow.events:return V2QuestItemStoreResult(False,"already_collected",self.uow.get(collection.key))
        current=self.uow.get(collection.key);updated=replace(current,quantity=current.quantity+collection.quantity,revision=current.revision+1)
        self.uow.put(updated);self.uow.events.add(identity);return V2QuestItemStoreResult(True,balance=updated)
    def consume(self,key:V2QuestItemBalanceKey,quantity:int,expected_revision:int)->V2QuestItemStoreResult:
        if quantity<=0:return V2QuestItemStoreResult(False,"invalid_quantity",self.uow.get(key))
        current=self.uow.get(key)
        if current.revision!=expected_revision:return V2QuestItemStoreResult(False,"stale_revision",current)
        if current.quantity<quantity:return V2QuestItemStoreResult(False,"insufficient_quantity",current)
        updated=replace(current,quantity=current.quantity-quantity,revision=current.revision+1);self.uow.put(updated)
        return V2QuestItemStoreResult(True,balance=updated,consumed=quantity)
    def plan_turn_in(self,plan:V2QuestItemTurnInPlan)->V2QuestItemStoreResult:
        if plan.completion_key in self.uow.completions:return V2QuestItemStoreResult(False,"already_completed",self.uow.get(plan.key))
        return self.consume(plan.key,plan.required_quantity,plan.expected_revision)
    def commit_turn_in(self,plan:V2QuestItemTurnInPlan)->None:self.uow.completions.add(plan.completion_key)
    def skip(self,key:V2QuestItemBalanceKey)->V2QuestItemStoreResult:
        return V2QuestItemStoreResult(True,"preserved_on_skip",self.uow.get(key))
