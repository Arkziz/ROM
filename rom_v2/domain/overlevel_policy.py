"""Pure Stage 19.18 overlevel policy records and invariants."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

LOCATION_MAX_LEVELS=MappingProxyType({"start_path":5,"dark_forest":10})
class OverlevelQuestStatus(str,Enum):
 ACTIVE="ACTIVE";COMPLETED="COMPLETED";SKIPPED="SKIPPED"
FINALIZED_STATUSES=frozenset({OverlevelQuestStatus.COMPLETED,OverlevelQuestStatus.SKIPPED})
@dataclass(frozen=True,slots=True)
class OverlevelQuestDefinition:
 quest_id:str;number:int;location_id:str;target_quantity:int=1
 def __post_init__(self):
  if not self.quest_id or self.number<1 or self.location_id not in LOCATION_MAX_LEVELS or self.target_quantity<1:raise ValueError("invalid_overlevel_quest_definition")
@dataclass(frozen=True,slots=True)
class OverlevelQuestRow:
 quest_id:str;number:int;location_id:str;status:OverlevelQuestStatus;progress:int;target_quantity:int;reward_claimed:bool=False
 def __post_init__(self):
  if self.progress<0 or self.target_quantity<1 or self.progress>self.target_quantity:raise ValueError("invalid_overlevel_quest_row")
  if self.status==OverlevelQuestStatus.SKIPPED and self.reward_claimed:raise ValueError("skipped_quest_cannot_claim_reward")
@dataclass(frozen=True,slots=True)
class OverlevelLocationResult:
 location_id:str;max_level:int;completed:int;already_skipped:int;skipped_now:int;quest_items_deleted:int
@dataclass(frozen=True,slots=True)
class OverlevelReconciliationResult:
 current_level:int;changed:int;locations:tuple[OverlevelLocationResult,...]
 @property
 def exceeded_locations(self):return tuple(x.location_id for x in self.locations)
def is_location_exceeded(current_level:int,location_id:str,max_levels=LOCATION_MAX_LEVELS)->bool:
 if location_id not in max_levels:raise KeyError("unknown_story_location")
 return int(current_level)>int(max_levels[location_id])
