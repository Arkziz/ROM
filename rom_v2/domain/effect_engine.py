"""Pure transient status-effect lifecycle for ROM V2.

The engine returns immutable transition results. It does not perform persistence,
HP/resource writes, presentation, resistance/immunity, or runtime dispatch.
Context adapters choose reapplication policy to preserve V1-specific behavior.
"""
from __future__ import annotations
from dataclasses import dataclass,field,replace
from enum import Enum
from types import MappingProxyType
from typing import Mapping
class EffectKind(str,Enum):DOT="dot";HOT="hot";SHIELD="shield";MODIFIER="modifier"
class ReapplyPolicy(str,Enum):REPLACE="replace";STRONGER_LONGER="stronger_longer"
class ApplyOutcome(str,Enum):APPLIED="applied";REPLACED="replaced";REFRESHED="refreshed";KEPT_STRONGER="kept_stronger";UNCHANGED="unchanged";REJECTED="rejected"
class EffectEventKind(str,Enum):DAMAGE="damage";HEAL="heal";SHIELD_ABSORB="shield_absorb";EXPIRED="expired"
@dataclass(frozen=True)
class Effect:
 key:str;kind:EffectKind;turns:int;power:int=0;modifiers:Mapping[str,int]=field(default_factory=dict);fresh:bool=False
 def __post_init__(self):
  if not self.key.strip():raise ValueError("effect key must not be empty")
  if self.turns<=0 or self.power<0:raise ValueError("turns must be positive and power non-negative")
  object.__setattr__(self,"modifiers",MappingProxyType(dict(self.modifiers)))
@dataclass(frozen=True)
class EffectEvent:kind:EffectEventKind;effect_key:str;amount:int=0
@dataclass(frozen=True)
class EffectTransition:
 effects:Mapping[str,Effect];events:tuple[EffectEvent,...]=();outcome:ApplyOutcome|None=None;success:bool=True;reason:str|None=None
 def __post_init__(self):object.__setattr__(self,"effects",MappingProxyType(dict(self.effects)))
def _snapshot(effects:Mapping[str,Effect])->dict[str,Effect]:return dict(effects)
def _strength(effect:Effect)->int:return max([effect.power,*[abs(int(v)) for v in effect.modifiers.values()]],default=0)
def apply_effect(effects:Mapping[str,Effect],incoming:Effect,policy:ReapplyPolicy)->EffectTransition:
 """Return a complete same-key apply/reapply transition without mutating input."""
 current=_snapshot(effects);existing=current.get(incoming.key)
 if existing is None:current[incoming.key]=incoming;return EffectTransition(current,outcome=ApplyOutcome.APPLIED)
 if policy is ReapplyPolicy.REPLACE:current[incoming.key]=incoming;return EffectTransition(current,outcome=ApplyOutcome.REPLACED)
 old_power,new_power=_strength(existing),_strength(incoming)
 if new_power<old_power:return EffectTransition(current,outcome=ApplyOutcome.KEPT_STRONGER)
 if new_power==old_power:
  if incoming.turns>existing.turns:current[incoming.key]=replace(existing,turns=incoming.turns);return EffectTransition(current,outcome=ApplyOutcome.REFRESHED)
  return EffectTransition(current,outcome=ApplyOutcome.UNCHANGED)
 current[incoming.key]=replace(incoming,turns=max(existing.turns,incoming.turns),fresh=existing.fresh or incoming.fresh)
 return EffectTransition(current,outcome=ApplyOutcome.REPLACED)
def remove_effect(effects:Mapping[str,Effect],key:str)->EffectTransition:
 current=_snapshot(effects)
 if key not in current:return EffectTransition(current,outcome=ApplyOutcome.UNCHANGED)
 del current[key];return EffectTransition(current,outcome=ApplyOutcome.REPLACED)
def tick_start(effects:Mapping[str,Effect])->EffectTransition:
 """Apply DOT/HOT ticks, then decrement and expire; fresh effects skip one tick."""
 current=_snapshot(effects);events=[]
 for key,effect in list(current.items()):
  if effect.fresh:current[key]=replace(effect,fresh=False);continue
  if effect.kind is EffectKind.DOT and effect.power:events.append(EffectEvent(EffectEventKind.DAMAGE,key,effect.power))
  elif effect.kind is EffectKind.HOT and effect.power:events.append(EffectEvent(EffectEventKind.HEAL,key,effect.power))
  turns=effect.turns-1
  if turns<=0:del current[key];events.append(EffectEvent(EffectEventKind.EXPIRED,key))
  else:current[key]=replace(effect,turns=turns)
 return EffectTransition(current,tuple(events))
def absorb_shield(effects:Mapping[str,Effect],damage:int)->tuple[int,EffectTransition]:
 """Consume shields in stable insertion order and return residual damage."""
 if damage<0:return damage,EffectTransition(_snapshot(effects),success=False,reason="negative_damage")
 current=_snapshot(effects);events=[];remaining=damage
 for key,effect in list(current.items()):
  if remaining<=0:break
  if effect.kind is not EffectKind.SHIELD or effect.power<=0:continue
  absorbed=min(remaining,effect.power);remaining-=absorbed;left=effect.power-absorbed;events.append(EffectEvent(EffectEventKind.SHIELD_ABSORB,key,absorbed))
  if left<=0:del current[key];events.append(EffectEvent(EffectEventKind.EXPIRED,key))
  else:current[key]=replace(effect,power=left)
 return remaining,EffectTransition(current,tuple(events))
