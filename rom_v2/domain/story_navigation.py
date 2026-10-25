"""Pure domain records and invariants for V2 Story navigation."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

FORBIDDEN_UI_TERMS=("глава","глави","главу","главою","главі")
class StoryQuestStatus(str,Enum):
 ACTIVE="ACTIVE";COMPLETED="COMPLETED";SKIPPED="SKIPPED";AVAILABLE="AVAILABLE";LOCKED="LOCKED"
@dataclass(frozen=True,slots=True)
class StoryQuestState:
 quest_number:int;status:StoryQuestStatus;progress:int=0;target_quantity:int=1;quest_item_quantity:int=0
 def __post_init__(self):
  if self.quest_number<1 or self.progress<0 or self.target_quantity<1 or self.quest_item_quantity<0:raise ValueError("invalid_story_quest_state")
  if self.progress>self.target_quantity:raise ValueError("progress_exceeds_target")
@dataclass(frozen=True,slots=True)
class StoryQuestView:
 number:int;quest_id:str;title:str;status:StoryQuestStatus;progress:int;target_quantity:int;actionable:bool
@dataclass(frozen=True,slots=True)
class StorySectionView:
 section_id:str;location_id:str;number:int;title:str;required_level:int;quests:tuple[StoryQuestView,...]
 @property
 def display_title(self):return f"Розділ {self.number}. {self.title}"
@dataclass(frozen=True,slots=True)
class StoryView:
 story_id:str;location_id:str;display_name:str;icon:str;sections:tuple[StorySectionView,...]
def ensure_safe_ui_text(text:str)->str:
 value=str(text)
 folded=value.casefold()
 if any(term in folded for term in FORBIDDEN_UI_TERMS):raise ValueError("forbidden_story_navigation_term")
 if "start_path" in value or "dark_forest" in value:raise ValueError("technical_location_id_exposed")
 return value
