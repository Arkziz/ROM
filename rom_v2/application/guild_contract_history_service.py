"""Pure guild contract reward and history application services."""
from __future__ import annotations
from dataclasses import dataclass
from rom_v2.domain.guild_contract_history import GuildHistoryEvent,GuildHistoryPage
@dataclass(frozen=True,slots=True)
class ContractRewardResult:
 success:bool;reason:str|None=None;guild_id:int|None=None;event_id:int|None=None;already_applied:bool=False
class GuildContractHistoryService:
 def __init__(self,uow):self.uow=uow
 def apply(self,completion):
  previous=self.uow.claim_result(completion.completion_key)
  if previous is not None:return ContractRewardResult(True,guild_id=previous.guild_id,event_id=previous.event_id,already_applied=True)
  guild=self.uow.guild_for_user(completion.user_id)
  if guild is None:return ContractRewardResult(False,"not_in_guild")
  try:
   event=GuildHistoryEvent(self.uow.next_event_id(),guild.guild_id,"contract_completed",completion.target_name.strip(),completion.actor_name)
   self.uow.add_progress(guild.guild_id,completion.user_id,contracts=1)
   self.uow.append_event(event);result=ContractRewardResult(True,guild_id=guild.guild_id,event_id=event.event_id)
   self.uow.save_claim(completion.completion_key,result);self.uow.commit();return result
  except Exception:self.uow.rollback();raise
 def history(self,user_id,guild_id,limit=20,offset=0):
  guild=self.uow.guild(guild_id)
  if guild is None:return None,"guild_not_found"
  if guild.role_of(user_id) is None:return None,"permission_denied"
  size=max(1,min(100,int(limit)));start=max(0,int(offset));items=tuple(self.uow.events(guild_id,start,size));return GuildHistoryPage(guild_id,items,self.uow.event_count(guild_id),size,start),None
class MemoryContractHistoryUow:
 def __init__(self,guilds):self.guilds={g.guild_id:g for g in guilds};self.claims={};self.history_rows=[];self.progress=[];self.sequence=0;self.commits=0;self.rollbacks=0
 def guild(self,i):return self.guilds.get(i)
 def guild_for_user(self,u):return next((g for g in self.guilds.values() if g.role_of(u) is not None),None)
 def claim_result(self,k):return self.claims.get(k)
 def save_claim(self,k,r):self.claims[k]=r
 def next_event_id(self):self.sequence+=1;return self.sequence
 def add_progress(self,g,u,contracts):self.progress.append((g,u,contracts))
 def append_event(self,e):self.history_rows.append(e)
 def events(self,g,offset,limit):return sorted((e for e in self.history_rows if e.guild_id==g),key=lambda e:e.event_id,reverse=True)[offset:offset+limit]
 def event_count(self,g):return sum(e.guild_id==g for e in self.history_rows)
 def commit(self):self.commits+=1
 def rollback(self):self.rollbacks+=1
