"""Pure canonical skill-execution orchestration for ROM V2.

The module owns validation and ordering only. Damage, resource debit, cooldown
storage, special effects, persistence and presentation are injected policies so
this layer cannot duplicate their formulas or mutate external state partially.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from enum import Enum
from typing import Callable,Mapping,Protocol
from rom_v2.domain.damage_engine import DamageType
class SkillKind(str,Enum):BASIC_ATTACK="basic_attack";ACTIVE="active"
class FailureReason(str,Enum):UNKNOWN_SKILL="unknown_skill";UNAVAILABLE="unavailable";INSUFFICIENT_RESOURCE="insufficient_resource";ON_COOLDOWN="on_cooldown";MISS="miss";EFFECT_REJECTED="effect_rejected"
@dataclass(frozen=True)
class SkillDefinition:
 key:str;kind:SkillKind;cost:int=0;cooldown:int=0;damage_type:DamageType|None=None
 def __post_init__(self):
  if not self.key.strip():raise ValueError("skill key must not be empty")
  if self.cost<0 or self.cooldown<0:raise ValueError("cost and cooldown must be non-negative")
@dataclass(frozen=True)
class SkillRequest:skill_key:str;actor_class:str
@dataclass(frozen=True)
class SkillExecution:
 success:bool;skill_key:str;damage_type:DamageType|None=None;cost_paid:int=0;cooldown_applied:int=0;hit:bool=False;effects:Mapping[str,int|str|bool]=field(default_factory=dict);failure:FailureReason|None=None
class ResourcePolicy(Protocol):
 def can_pay(self,cost:int)->bool:...
 def pay(self,cost:int)->None:...
class CooldownPolicy(Protocol):
 def remaining(self,skill_key:str)->int:...
 def start(self,skill_key:str,turns:int)->None:...
Availability=Callable[[SkillDefinition],bool];HitPolicy=Callable[[SkillDefinition,DamageType],bool];EffectPolicy=Callable[[SkillDefinition,DamageType],Mapping[str,int|str|bool]|None];BasicAttackRouter=Callable[[str],DamageType]
def execute_skill(request:SkillRequest,catalog:Mapping[str,SkillDefinition],resource:ResourcePolicy,cooldowns:CooldownPolicy,availability:Availability,hit_policy:HitPolicy,effect_policy:EffectPolicy,basic_attack_router:BasicAttackRouter)->SkillExecution:
 """Validate first, then perform ordered exact-once payment, effect and cooldown.

 No mutation occurs for unknown, unavailable, insufficient-resource, cooldown,
 miss, or rejected-effect outcomes. Payment and cooldown happen only after all
 pure checks and effect preparation succeed.
 """
 skill=catalog.get(request.skill_key)
 if skill is None:return SkillExecution(False,request.skill_key,failure=FailureReason.UNKNOWN_SKILL)
 if not availability(skill):return SkillExecution(False,skill.key,failure=FailureReason.UNAVAILABLE)
 if not resource.can_pay(skill.cost):return SkillExecution(False,skill.key,failure=FailureReason.INSUFFICIENT_RESOURCE)
 if cooldowns.remaining(skill.key)>0:return SkillExecution(False,skill.key,failure=FailureReason.ON_COOLDOWN)
 dtype=basic_attack_router(request.actor_class) if skill.kind is SkillKind.BASIC_ATTACK else skill.damage_type
 if dtype is None:raise ValueError("active damaging skill requires an explicit damage type")
 if not hit_policy(skill,dtype):return SkillExecution(False,skill.key,damage_type=dtype,failure=FailureReason.MISS)
 effects=effect_policy(skill,dtype)
 if effects is None:return SkillExecution(False,skill.key,damage_type=dtype,failure=FailureReason.EFFECT_REJECTED)
 resource.pay(skill.cost);cooldowns.start(skill.key,skill.cooldown)
 return SkillExecution(True,skill.key,dtype,skill.cost,skill.cooldown,True,dict(effects))
