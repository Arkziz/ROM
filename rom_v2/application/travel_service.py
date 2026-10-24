from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
from rom_v2.content.location_catalog import is_location_unlocked
from rom_v2.content.world_graph import CITY_NODE_ID,TRAVEL_SECONDS,are_adjacent,get_world_node
from rom_v2.domain.travel_aggregate import TravelAggregate,TravelStatus
@dataclass(frozen=True,slots=True)
class TravelResult:success:bool;reason:str|None=None;travel:TravelAggregate|None=None;location:str|None=None
class TravelService:
 def __init__(self,uow,busy):self.uow=uow;self.busy=busy
 def _utc(self,n):
  if n.tzinfo is None:raise ValueError("aware UTC required")
  return n.astimezone(timezone.utc)
 def start(self,user_id,to_node,now):
  if self.busy.get_busy(user_id):return TravelResult(False,"player_busy")
  now=self._utc(now)
  try:
   p=self.uow.get_player(user_id)
   if p is None:return TravelResult(False,"user_not_found")
   source=str(p["location"] or CITY_NODE_ID);target=str(to_node)
   if get_world_node(source) is None:return TravelResult(False,"invalid_current_node")
   if get_world_node(target) is None:return TravelResult(False,"unknown_destination")
   if not are_adjacent(source,target):return TravelResult(False,"not_adjacent")
   if target!=CITY_NODE_ID and not is_location_unlocked(target,int(p["level"] or 1)):return TravelResult(False,"location_locked")
   if self.uow.get_active(user_id):return TravelResult(False,"already_travelling")
   t=TravelAggregate(self.uow.next_id(),user_id,source,target,TravelStatus.ACTIVE,1,now,now+timedelta(seconds=TRAVEL_SECONDS));self.uow.save(t);self.uow.commit();return TravelResult(True,travel=t)
  except Exception:self.uow.rollback();raise
 def cancel(self,user_id,travel_id,revision,now):
  now=self._utc(now);t=self.uow.get(travel_id)
  if t is None:return TravelResult(False,"travel_not_found")
  changed,reason=t.cancel(user_id,revision,now)
  if changed is None:return TravelResult(False,reason,t)
  self.uow.save(changed);self.uow.commit();return TravelResult(True,travel=changed)
 def complete(self,travel_id,now):
  now=self._utc(now);t=self.uow.get(travel_id)
  if t is None:return TravelResult(False,"travel_not_found")
  p=self.uow.get_player(t.user_id)
  if p is None:return TravelResult(False,"user_not_found")
  changed,reason=t.complete(str(p["location"] or CITY_NODE_ID),now)
  if changed is None:return TravelResult(False,reason,t)
  if changed.status is TravelStatus.FAILED:self.uow.save(changed);self.uow.commit();return TravelResult(False,reason,changed)
  if not self.uow.cas_location(t.user_id,t.from_node,t.to_node):return TravelResult(False,"terminal_claim_lost",t)
  self.uow.save(changed);self.uow.commit();return TravelResult(True,travel=changed,location=t.to_node)
 def recover_due(self,now,limit=100):return tuple(self.complete(t.travel_id,now) for t in self.uow.due(self._utc(now),max(1,min(100,int(limit)))))
class MemoryBusy:
 def __init__(self):self.data={}
 def get_busy(self,u):return self.data.get(u)
class MemoryUow:
 def __init__(self,players):self.players={k:dict(v) for k,v in players.items()};self.travels={};self.seq=0;self.commits=0;self.rollbacks=0
 def get_player(self,u):return self.players.get(u)
 def get_active(self,u):return next((t for t in self.travels.values() if t.user_id==u and t.status is TravelStatus.ACTIVE),None)
 def get(self,i):return self.travels.get(i)
 def next_id(self):self.seq+=1;return self.seq
 def save(self,t):self.travels[t.travel_id]=t
 def cas_location(self,u,e,v):
  p=self.players.get(u)
  if p is None or str(p["location"] or CITY_NODE_ID)!=e:return False
  p["location"]=v;return True
 def due(self,n,l):return sorted((t for t in self.travels.values() if t.status is TravelStatus.ACTIVE and t.arrival_at<=n),key=lambda t:(t.arrival_at,t.travel_id))[:l]
 def commit(self):self.commits+=1
 def rollback(self):self.rollbacks+=1
