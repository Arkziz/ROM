"""Pure Guild Applications/Management service and in-memory fixtures."""
from __future__ import annotations
from dataclasses import dataclass,replace
from rom_v2.domain.guild_application import ApplicationStatus,GuildApplication
from rom_v2.domain.guild_core import GuildCore,GuildMember,GuildRole,MINIMUM_ACCESS_LEVEL
@dataclass(frozen=True,slots=True)
class ManagementResult:
 success:bool; reason:str|None=None; application:GuildApplication|None=None; guild:GuildCore|None=None
class GuildManagementService:
 def __init__(self,uow):self.uow=uow
 @staticmethod
 def _manager(role):return role in {GuildRole.LEADER,GuildRole.OFFICER}
 def accept(self,actor_id,application_id):
  app=self.uow.application(application_id)
  if app is None:return ManagementResult(False,"application_not_found")
  guild=self.uow.guild(app.guild_id);role=guild.role_of(actor_id) if guild else None
  if not self._manager(role):return ManagementResult(False,"permission_denied",app,guild)
  if app.status is not ApplicationStatus.PENDING:return ManagementResult(False,"already_processed",app,guild)
  if self.uow.guild_for_user(app.user_id):return ManagementResult(False,"already_in_guild",app,guild)
  if self.uow.level(app.user_id)<MINIMUM_ACCESS_LEVEL:return ManagementResult(False,"level_too_low",app,guild)
  if not self.uow.join_allowed(app.user_id):return ManagementResult(False,"join_cooldown",app,guild)
  if len(guild.members)>=guild.member_limit:return ManagementResult(False,"member_limit_reached",app,guild)
  try:
   claimed,reason=app.decide(actor_id,ApplicationStatus.ACCEPTED)
   if claimed is None:return ManagementResult(False,reason,app,guild)
   changed=replace(guild,members=guild.members+(GuildMember(app.user_id,GuildRole.MEMBER),))
   self.uow.save_application(claimed);self.uow.save_guild(changed);self.uow.commit();return ManagementResult(True,application=claimed,guild=changed)
  except Exception:self.uow.rollback();raise
 def reject(self,actor_id,application_id):
  app=self.uow.application(application_id)
  if app is None:return ManagementResult(False,"application_not_found")
  guild=self.uow.guild(app.guild_id);role=guild.role_of(actor_id) if guild else None
  if not self._manager(role):return ManagementResult(False,"permission_denied",app,guild)
  changed,reason=app.decide(actor_id,ApplicationStatus.REJECTED)
  if changed is None:return ManagementResult(False,reason,app,guild)
  self.uow.save_application(changed);self.uow.commit();return ManagementResult(True,application=changed,guild=guild)
 def promote(self,actor_id,target_id):
  guild=self.uow.guild_for_user(actor_id)
  if guild is None:return ManagementResult(False,"not_in_guild")
  if guild.role_of(actor_id) is not GuildRole.LEADER:return ManagementResult(False,"permission_denied",guild=guild)
  if actor_id==target_id:return ManagementResult(False,"self_target",guild=guild)
  role=guild.role_of(target_id)
  if role is None:return ManagementResult(False,"target_not_member",guild=guild)
  if role is GuildRole.LEADER:return ManagementResult(False,"target_is_leader",guild=guild)
  if role is GuildRole.OFFICER:return ManagementResult(False,"already_officer",guild=guild)
  if sum(m.role is GuildRole.OFFICER for m in guild.members)>=self.uow.officer_limit(guild.guild_id):return ManagementResult(False,"officer_limit_reached",guild=guild)
  changed=replace(guild,members=tuple(GuildMember(m.user_id,GuildRole.OFFICER if m.user_id==target_id else m.role) for m in guild.members));self.uow.save_guild(changed);self.uow.commit();return ManagementResult(True,guild=changed)
 def kick(self,actor_id,target_id):
  guild=self.uow.guild_for_user(actor_id)
  if guild is None:return ManagementResult(False,"not_in_guild")
  actor=guild.role_of(actor_id);target=guild.role_of(target_id)
  if target is None:return ManagementResult(False,"target_not_member",guild=guild)
  if actor_id==target_id:return ManagementResult(False,"self_target",guild=guild)
  if target is GuildRole.LEADER:return ManagementResult(False,"target_is_leader",guild=guild)
  allowed=actor is GuildRole.LEADER or (actor is GuildRole.OFFICER and target is GuildRole.MEMBER)
  if not allowed:return ManagementResult(False,"permission_denied",guild=guild)
  changed=replace(guild,members=tuple(m for m in guild.members if m.user_id!=target_id));self.uow.save_guild(changed);self.uow.record_departure(target_id,guild.guild_id,"kicked",actor_id);self.uow.commit();return ManagementResult(True,guild=changed)
class MemoryManagementUow:
 def __init__(self,guilds,applications,levels,officer_limits):self.guilds={g.guild_id:g for g in guilds};self.applications={a.application_id:a for a in applications};self.levels=dict(levels);self.cooldowns=set();self.officer_limits=dict(officer_limits);self.departures=[];self.commits=0;self.rollbacks=0
 def application(self,i):return self.applications.get(i)
 def guild(self,i):return self.guilds.get(i)
 def guild_for_user(self,u):return next((g for g in self.guilds.values() if g.role_of(u) is not None),None)
 def level(self,u):return self.levels.get(u,0)
 def join_allowed(self,u):return u not in self.cooldowns
 def officer_limit(self,g):return self.officer_limits[g]
 def save_application(self,a):self.applications[a.application_id]=a
 def save_guild(self,g):self.guilds[g.guild_id]=g
 def record_departure(self,u,g,event,actor):self.departures.append((u,g,event,actor))
 def commit(self):self.commits+=1
 def rollback(self):self.rollbacks+=1
