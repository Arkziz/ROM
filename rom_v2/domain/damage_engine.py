"""Canonical V1-parity damage engine for PvE, PvP and simulation consumers."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol
DEFENSE_STAT_COEFFICIENT=0.35
DAMAGE_DEFENSE_COEFFICIENT=0.5
MINIMUM_DAMAGE=1
CRITICAL_DAMAGE_MULTIPLIER=1.5
CRIT_BASE_CHANCE=5.0
CRIT_STAT_BASELINE=10.0
CRIT_PER_STAT=0.35
CRIT_MIN_CHANCE=1.0
CRIT_SOFT_CAP_TRANSITION_STAT=50.0
CRIT_SOFT_CAP_TRANSITION_CHANCE=19.0
CRIT_SOFT_CAP_ASYMPTOTE=60.0
CRIT_SOFT_CAP_RANGE=41.0
CRIT_SOFT_CAP_K=41.0
DODGE_BASE_CHANCE=5.0
DODGE_PER_DEX_DELTA=0.2
DODGE_MIN_CHANCE=1.0
DODGE_SOFT_CAP_TRANSITION_DELTA=40.0
DODGE_SOFT_CAP_TRANSITION_CHANCE=13.0
DODGE_SOFT_CAP_ASYMPTOTE=50.0
DODGE_SOFT_CAP_RANGE=37.0
DODGE_SOFT_CAP_K=37.0
class DamageType(str,Enum):PHYSICAL="PHYSICAL";MAGICAL="MAGICAL"
class DamageRandomSource(Protocol):
 def random(self)->float:...
@dataclass(frozen=True,slots=True)
class DamageRequest:
 damage_type:DamageType;attack:float;defense:float;critical_chance:float=0.0;evasion_chance:float=0.0;damage_multiplier:float=1.0
 def __post_init__(self):
  if min(self.attack,self.defense,self.critical_chance,self.evasion_chance)<0 or self.damage_multiplier<0:raise ValueError("invalid_damage_request")
@dataclass(frozen=True,slots=True)
class DamageResult:
 damage:int;critical:bool;evaded:bool;raw_damage:float;mitigated_damage:float

def damage_clamp_chance(value:float,minimum:float,maximum:float)->float:return max(float(minimum),min(float(maximum),float(value)))
def damage_calculate_stat_defense(primary_stat:float)->float:return max(0.0,float(primary_stat))*DEFENSE_STAT_COEFFICIENT
def damage_total_defense(item_defense:float,primary_stat:float)->float:return max(0.0,float(item_defense))+damage_calculate_stat_defense(primary_stat)
def damage_after_defense(attack:float,defense:float)->float:return max(float(MINIMUM_DAMAGE),float(attack)-max(0.0,float(defense))*DAMAGE_DEFENSE_COEFFICIENT)
def damage_crit_chance(total_stat:float)->float:
 stat=float(total_stat or 0)
 if stat<=CRIT_SOFT_CAP_TRANSITION_STAT:return damage_clamp_chance(CRIT_BASE_CHANCE+max(0.0,stat-CRIT_STAT_BASELINE)*CRIT_PER_STAT,CRIT_MIN_CHANCE,CRIT_SOFT_CAP_ASYMPTOTE)
 excess=stat-CRIT_SOFT_CAP_TRANSITION_STAT
 return CRIT_SOFT_CAP_TRANSITION_CHANCE+CRIT_SOFT_CAP_RANGE*excess/(excess+CRIT_SOFT_CAP_K)
def damage_dodge_chance(defender_dex:float,attacker_dex:float)->float:
 delta=float(defender_dex or 0)-float(attacker_dex or 0)
 if delta<=-20:return DODGE_MIN_CHANCE
 if delta<=DODGE_SOFT_CAP_TRANSITION_DELTA:return DODGE_BASE_CHANCE+delta*DODGE_PER_DEX_DELTA
 excess=delta-DODGE_SOFT_CAP_TRANSITION_DELTA
 return DODGE_SOFT_CAP_TRANSITION_CHANCE+DODGE_SOFT_CAP_RANGE*excess/(excess+DODGE_SOFT_CAP_K)
def damage_enemy_crit_chance(player_sta:float)->float:return damage_clamp_chance(10.0-(int(player_sta or 0)//25),0.0,10.0)
def damage_roll_chance(chance:float,rng:DamageRandomSource)->bool:return rng.random()*100.0<damage_clamp_chance(chance,0.0,100.0)
def resolve_damage(request:DamageRequest,rng:DamageRandomSource)->DamageResult:
 """Resolve evasion, mitigation, critical multiplier and final V1 rounding once."""
 if damage_roll_chance(request.evasion_chance,rng):return DamageResult(0,False,True,request.attack,0.0)
 mitigated=damage_after_defense(request.attack,request.defense)
 critical=damage_roll_chance(request.critical_chance,rng)
 scaled=mitigated*request.damage_multiplier*(CRITICAL_DAMAGE_MULTIPLIER if critical else 1.0)
 return DamageResult(max(MINIMUM_DAMAGE,round(scaled)),critical,False,request.attack,mitigated)
