"""Pure Guild Core aggregate and invariants for V1 parity."""
from __future__ import annotations
from dataclasses import dataclass,replace
from enum import StrEnum
CREATION_COST_GOLD=50.0
MINIMUM_ACCESS_LEVEL=3
DEFAULT_MEMBER_LIMIT=10
class GuildRole(StrEnum):LEADER="leader";OFFICER="officer";MEMBER="member"
@dataclass(frozen=True,slots=True)
class GuildIdentity:
 name:str;name_key:str;tag:str;tag_key:str;icon:str
 def __post_init__(self):
  if not all((self.name,self.name_key,self.tag,self.tag_key,self.icon)):raise ValueError("invalid_identity")
@dataclass(frozen=True,slots=True)
class GuildMember:
 user_id:int;role:GuildRole
 def __post_init__(self):
  if self.user_id<1:raise ValueError("invalid_user_id")
@dataclass(frozen=True,slots=True)
class GuildCore:
 guild_id:int;identity:GuildIdentity;leader_user_id:int;members:tuple[GuildMember,...];member_limit:int=DEFAULT_MEMBER_LIMIT
 def __post_init__(self):self.validate()
 def validate(self):
  if self.guild_id<1 or self.member_limit<1:raise ValueError("invalid_guild")
  ids=[m.user_id for m in self.members]
  if len(ids)!=len(set(ids)):raise ValueError("duplicate_membership")
  if len(ids)>self.member_limit:raise ValueError("member_limit_reached")
  leaders=[m.user_id for m in self.members if m.role is GuildRole.LEADER]
  if leaders!=[self.leader_user_id]:raise ValueError("leader_invariant_broken")
 def role_of(self,user_id):return next((m.role for m in self.members if m.user_id==user_id),None)
 def can(self,user_id,permission):
  role=self.role_of(user_id)
  matrix={GuildRole.LEADER:{"manage_applications","manage_roles","manage_members","transfer","leave","dissolve"},GuildRole.OFFICER:{"manage_applications"},GuildRole.MEMBER:set()}
  return role is not None and permission in matrix[role]
 def transfer(self,actor_id,target_id):
  if actor_id!=self.leader_user_id:return None,"permission_denied"
  if target_id==actor_id:return None,"target_is_leader"
  if self.role_of(target_id) is None:return None,"target_not_member"
  changed=tuple(GuildMember(m.user_id,GuildRole.LEADER if m.user_id==target_id else GuildRole.MEMBER if m.user_id==actor_id else m.role) for m in self.members)
  return replace(self,leader_user_id=target_id,members=changed),None
 def leave(self,user_id):
  role=self.role_of(user_id)
  if role is None:return None,"not_in_guild"
  if role is GuildRole.LEADER and len(self.members)>1:return None,"leadership_transfer_required"
  if role is GuildRole.LEADER:return None,"dissolve_required"
  return replace(self,members=tuple(m for m in self.members if m.user_id!=user_id)),None
