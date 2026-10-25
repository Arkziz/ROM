"""Generic Quest Engine contracts independent from concrete quest content."""
from dataclasses import dataclass
from enum import StrEnum
class V2QuestObjectiveType(StrEnum): TALK="TALK";KILL_REGION="KILL_REGION";QUEST_ITEM="QUEST_ITEM";TURN_IN="TURN_IN";BOSS="BOSS"
class V2QuestState(StrEnum): UNAVAILABLE="unavailable";AVAILABLE="available";ACTIVE="active";READY_TO_TURN_IN="ready_to_turn_in";COMPLETED="completed";SKIPPED="skipped"
@dataclass(frozen=True,slots=True)
class V2QuestReward:
 exp:int=0;gold:int=0;items:tuple[tuple[str,int],...]=()
@dataclass(frozen=True,slots=True)
class V2QuestDefinition:
 quest_id:int;location_id:str;order:int;objective_type:V2QuestObjectiveType;target:int=1;required_level:int=1;previous_quest_id:int|None=None;required_item_key:str|None=None;required_item_quantity:int=0;reward:V2QuestReward=V2QuestReward()
 def __post_init__(self):
  if self.quest_id<1 or not self.location_id or self.order<1 or self.target<1 or self.required_level<1 or self.required_item_quantity<0:raise ValueError("invalid_quest_definition")
@dataclass(frozen=True,slots=True)
class V2QuestProgress:
 user_id:int;quest_id:int;state:V2QuestState;progress:int=0;revision:int=1
@dataclass(frozen=True,slots=True)
class V2QuestResult:
 success:bool;reason:str|None=None;progress:V2QuestProgress|None=None;changed:bool=False;reward_planned:bool=False
