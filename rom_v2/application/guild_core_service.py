"""Guild Core application service with in-memory Unit of Work fixtures."""
from __future__ import annotations
from dataclasses import dataclass
from rom_v2.domain.guild_core import *
@dataclass(frozen=True,slots=True)
class GuildResult:
 success:bool;reason:str|None=None;guild:GuildCore|None=None;gold_balance:float|None=None;dissolved:bool=False
class GuildCoreService:
 def __init__(self,uow):self.uow=uow
 def create(self,user_id,level,identity):
  if level<MINIMUM_ACCESS_LEVEL:return GuildResult(False,"level_too_low")
  if self.uow.guild_for_user(user_id):return GuildResult(False,"already_in_guild")
  if self.uow.name_exists(identity.name_key):return GuildResult(False,"duplicate_name")
  if self.uow.tag_exists(identity.tag_key):return GuildResult(False,"duplicate_tag")
  if self.uow.gold(user_id)<CREATION_COST_GOLD:return GuildResult(False,"insufficient_gold")
  try:
   guild=GuildCore(self.uow.next_guild_id(),identity,user_id,(GuildMember(user_id,GuildRole.LEADER),),DEFAULT_MEMBER_LIMIT)
   self.uow.debit(user_id,CREATION_COST_GOLD);self.uow.save(guild);self.uow.commit();return GuildResult(True,guild=guild,gold_balance=self.uow.gold(user_id))
  except Exception:self.uow.rollback();raise
 def transfer(self,actor_id,target_id):
  guild=self.uow.guild_for_user(actor_id)
  if guild is None:return GuildResult(False,"not_in_guild")
  changed,reason=guild.transfer(actor_id,target_id)
  if changed is None:return GuildResult(False,reason,guild)
  self.uow.save(changed);self.uow.commit();return GuildResult(True,guild=changed)
 def leave(self,user_id):
  guild=self.uow.guild_for_user(user_id)
  if guild is None:return GuildResult(False,"not_in_guild")
  changed,reason=guild.leave(user_id)
  if reason=="dissolve_required":self.uow.delete(guild.guild_id);self.uow.commit();return GuildResult(True,dissolved=True)
  if changed is None:return GuildResult(False,reason,guild)
  self.uow.save(changed);self.uow.commit();return GuildResult(True,guild=changed)
class MemoryGuildUow:
 def __init__(self,gold):self.gold_balances=dict(gold);self.guilds={};self.sequence=0;self.commits=0;self.rollbacks=0
 def next_guild_id(self):self.sequence+=1;return self.sequence
 def gold(self,u):return float(self.gold_balances.get(u,0.0))
 def debit(self,u,a):
  if self.gold(u)<a:raise ValueError("insufficient_gold")
  self.gold_balances[u]=round(self.gold(u)-a,2)
 def guild_for_user(self,u):return next((g for g in self.guilds.values() if g.role_of(u) is not None),None)
 def name_exists(self,k):return any(g.identity.name_key==k for g in self.guilds.values())
 def tag_exists(self,k):return any(g.identity.tag_key==k for g in self.guilds.values())
 def save(self,g):self.guilds[g.guild_id]=g
 def delete(self,i):self.guilds.pop(i,None)
 def commit(self):self.commits+=1
 def rollback(self):self.rollbacks+=1
