"""Pure PvP lifecycle contracts. Combat formulas remain in shared V1 policy adapters."""
from dataclasses import dataclass,replace
from enum import StrEnum
class V2PvpBattleStatus(StrEnum): ACTIVE="active";COMPLETED="completed";CANCELLED="cancelled"
@dataclass(frozen=True,slots=True)
class V2PvpParticipantSnapshot:
 user_id:int;side:str;class_key:str;level:int;max_hp:int;current_hp:int;resource_type:str;resource:int;combo:int=0
 def __post_init__(self):
  if self.user_id<1 or self.side not in {"a","b"} or self.level<1 or self.max_hp<1 or not 0<=self.current_hp<=self.max_hp:raise ValueError("invalid_snapshot")
@dataclass(frozen=True,slots=True)
class V2PvpBattleState:
 battle_id:int;request_id:int;participants:tuple[V2PvpParticipantSnapshot,V2PvpParticipantSnapshot];round_number:int=1;revision:int=1;status:V2PvpBattleStatus=V2PvpBattleStatus.ACTIVE;winner_id:int|None=None;result_reason:str|None=None;deadline_at:int=0
 def __post_init__(self):
  if min(self.battle_id,self.request_id,self.round_number,self.revision)<1 or self.participants[0].user_id==self.participants[1].user_id:raise ValueError("invalid_battle")
@dataclass(frozen=True,slots=True)
class V2PvpActionIntent:
 battle_id:int;round_number:int;revision:int;user_id:int;action_key:str
@dataclass(frozen=True,slots=True)
class V2PvpLifecycleResult:
 success:bool;reason:str|None=None;battle:V2PvpBattleState|None=None;changed:bool=False;resolution_required:bool=False
@dataclass(frozen=True,slots=True)
class V2PvpRecoveryOutcome: battle_id:int;outcome:str
