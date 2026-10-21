"""Canonical typed Rage and Energy policies for V2 combat consumers.

The module owns pure resource state transitions only. Skill execution, persistence,
presentation, Mana, Combo and battle orchestration remain external boundaries.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
RAGE_MAX=100
RAGE_START=0
RAGE_GAIN_ON_ATTACK=15
RAGE_GAIN_ON_DAMAGE_TAKEN=10
ENERGY_MAX=100
ENERGY_START=100
ENERGY_REGEN_PER_PLAYER_TURN=20
class CombatResourceFailure(str,Enum):
 INSUFFICIENT_RESOURCE="INSUFFICIENT_RESOURCE"
 INVALID_AMOUNT="INVALID_AMOUNT"
@dataclass(frozen=True,slots=True)
class RageState:
 current:int=RAGE_START
 maximum:int=RAGE_MAX
 def __post_init__(self)->None:
  if self.maximum<0 or not 0<=self.current<=self.maximum:raise ValueError("invalid_rage_state")
@dataclass(frozen=True,slots=True)
class EnergyState:
 current:int=ENERGY_START
 maximum:int=ENERGY_MAX
 def __post_init__(self)->None:
  if self.maximum<0 or not 0<=self.current<=self.maximum:raise ValueError("invalid_energy_state")
@dataclass(frozen=True,slots=True)
class RageTransition:
 success:bool
 state:RageState
 amount:int=0
 failure:CombatResourceFailure|None=None
@dataclass(frozen=True,slots=True)
class EnergyTransition:
 success:bool
 state:EnergyState
 amount:int=0
 failure:CombatResourceFailure|None=None

def _resource_amount(value:int)->int:
 if isinstance(value,bool) or not isinstance(value,int) or value<0:raise ValueError("invalid_resource_amount")
 return value
def rage_gain(state:RageState,amount:int)->RageTransition:
 """Add and clamp Rage, preserving the exact applied amount."""
 requested=_resource_amount(amount);current=min(state.maximum,state.current+requested)
 return RageTransition(True,RageState(current,state.maximum),current-state.current)
def rage_gain_on_attack(state:RageState)->RageTransition:return rage_gain(state,RAGE_GAIN_ON_ATTACK)
def rage_gain_on_damage_taken(state:RageState)->RageTransition:return rage_gain(state,RAGE_GAIN_ON_DAMAGE_TAKEN)
def rage_gain_from_skill(state:RageState,extra_rage:int)->RageTransition:return rage_gain(state,extra_rage)
def rage_spend(state:RageState,cost:int)->RageTransition:
 """Validate before debit; rejection returns the identical immutable state."""
 amount=_resource_amount(cost)
 if amount>state.current:return RageTransition(False,state,0,CombatResourceFailure.INSUFFICIENT_RESOURCE)
 return RageTransition(True,RageState(state.current-amount,state.maximum),amount)
def energy_regenerate_player_turn(state:EnergyState)->EnergyTransition:
 """Apply the canonical +20 Energy at player-turn start with max clamp."""
 current=min(state.maximum,state.current+ENERGY_REGEN_PER_PLAYER_TURN)
 return EnergyTransition(True,EnergyState(current,state.maximum),current-state.current)
def energy_spend(state:EnergyState,cost:int)->EnergyTransition:
 """Validate before debit; rejection returns the identical immutable state."""
 amount=_resource_amount(cost)
 if amount>state.current:return EnergyTransition(False,state,0,CombatResourceFailure.INSUFFICIENT_RESOURCE)
 return EnergyTransition(True,EnergyState(state.current-amount,state.maximum),amount)
def projected_energy_at_player_turn(state:EnergyState)->EnergyState:
 return energy_regenerate_player_turn(state).state
