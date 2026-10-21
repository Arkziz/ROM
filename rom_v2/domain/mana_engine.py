"""Canonical V1-parity Mana Engine shared by future runtime consumers."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal,InvalidOperation,ROUND_HALF_UP
from math import isfinite
from typing import Any,Mapping
MAX_MP_BASE=100
MAX_MP_PER_LEVEL=20
MAX_MP_PER_INT=1
MAX_MP_PER_WIS=4
MANA_POST_COMBAT_FLOOR_PERCENT=50
MANA_REGEN_PERCENT_PER_FULL_MINUTE=30
MANA_COST_FLAT_FIELD="mana_cost_flat"
MANA_COST_MAX_MP_PERCENT_FIELD="mana_cost_max_mp_percent"
MANA_RESTORE_MAX_MP_PERCENT_FIELD="restore_max_mp_percent"
class ManaEngineError(ValueError):pass
@dataclass(frozen=True,slots=True)
class ManaState:
 current_mp:int
 max_mp:int
 def __post_init__(self)->None:
  if self.max_mp<0 or not 0<=self.current_mp<=self.max_mp:raise ManaEngineError("invalid_mana_state")
@dataclass(frozen=True,slots=True)
class ManaTransition:
 success:bool
 state:ManaState
 amount:int=0
 reason:str|None=None

def _mana_decimal(value:Any,field:str)->Decimal:
 if isinstance(value,bool) or value is None:raise ManaEngineError(f"{field}_must_be_finite")
 if isinstance(value,float) and not isfinite(value):raise ManaEngineError(f"{field}_must_be_finite")
 try:number=Decimal(str(value))
 except (InvalidOperation,ValueError,TypeError) as error:raise ManaEngineError(f"{field}_must_be_finite") from error
 if not number.is_finite() or number<0:raise ManaEngineError(f"{field}_must_be_non_negative")
 return number
def mana_round_half_up(value:Any)->int:return int(_mana_decimal(value,"value").quantize(Decimal("1"),rounding=ROUND_HALF_UP))
def mana_calculate_max_mp(level:Any,intelligence:Any,wisdom:Any,is_mana_class:bool=True)->int:
 if not is_mana_class:return 0
 return max(0,int(MAX_MP_BASE+_mana_decimal(level,"level")*MAX_MP_PER_LEVEL+_mana_decimal(intelligence,"intelligence")*MAX_MP_PER_INT+_mana_decimal(wisdom,"wisdom")*MAX_MP_PER_WIS))
def mana_validate_skill_definition(skill:Mapping[str,Any])->dict[str,Decimal]:
 if not isinstance(skill,Mapping):raise ManaEngineError("skill_must_be_mapping")
 unknown={key for key in skill if key.startswith("mana_cost") and key not in {MANA_COST_FLAT_FIELD,MANA_COST_MAX_MP_PERCENT_FIELD}}
 if unknown:raise ManaEngineError("unsupported_mana_cost_fields")
 return {MANA_COST_FLAT_FIELD:_mana_decimal(skill.get(MANA_COST_FLAT_FIELD,0),MANA_COST_FLAT_FIELD),MANA_COST_MAX_MP_PERCENT_FIELD:_mana_decimal(skill.get(MANA_COST_MAX_MP_PERCENT_FIELD,0),MANA_COST_MAX_MP_PERCENT_FIELD)}
def mana_calculate_skill_cost(skill:Mapping[str,Any],max_mp:Any)->int:
 policy=mana_validate_skill_definition(skill);maximum=mana_round_half_up(max_mp)
 raw=policy[MANA_COST_FLAT_FIELD]+Decimal(maximum)*policy[MANA_COST_MAX_MP_PERCENT_FIELD]/Decimal("100")
 return mana_round_half_up(raw)
def mana_restore_amount(max_mp:Any,percent:Any)->int:
 maximum=mana_round_half_up(max_mp);amount=mana_round_half_up(Decimal(maximum)*_mana_decimal(percent,"percent")/Decimal("100"));return min(maximum,amount)
def mana_post_combat_floor(max_mp:Any)->int:return mana_restore_amount(max_mp,MANA_POST_COMBAT_FLOOR_PERCENT)
def mana_passive_regen_tick(max_mp:Any)->int:return mana_restore_amount(max_mp,MANA_REGEN_PERCENT_PER_FULL_MINUTE)
def mana_rebase_current(current_mp:Any,new_max_mp:Any)->ManaState:
 maximum=mana_round_half_up(new_max_mp);return ManaState(min(mana_round_half_up(current_mp),maximum),maximum)
def mana_spend(state:ManaState,cost:Any)->ManaTransition:
 amount=mana_round_half_up(cost)
 if amount>state.current_mp:return ManaTransition(False,state,0,"INSUFFICIENT_MANA")
 return ManaTransition(True,ManaState(state.current_mp-amount,state.max_mp),amount)
def mana_restore(state:ManaState,amount:Any)->ManaTransition:
 restored=min(mana_round_half_up(amount),state.max_mp-state.current_mp)
 return ManaTransition(True,ManaState(state.current_mp+restored,state.max_mp),restored)
def mana_apply_post_combat_floor(state:ManaState)->ManaTransition:
 target=max(state.current_mp,mana_post_combat_floor(state.max_mp));return ManaTransition(True,ManaState(target,state.max_mp),target-state.current_mp)
