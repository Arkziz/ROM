from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class V2ItemIdNamespace(str, Enum):
    STATIC = "static_catalog"
    EVENT = "event_static"
    GENERATED = "generated_permanent"
    PREVIEW = "shop_preview"
    STORY_KEY = "story_quest_key"

@dataclass(frozen=True, slots=True)
class V2NumericRange:
    start: int
    end: int
    def __post_init__(self):
        if self.start < 0 or self.end < self.start: raise ValueError("invalid_range")
    def contains(self, value: int) -> bool: return self.start <= value <= self.end
    @property
    def size(self) -> int: return self.end - self.start + 1

EVENT_RANGE=V2NumericRange(4000,9999)
GENERATED_RANGE=V2NumericRange(10000,10009999)
PREVIEW_RANGE=V2NumericRange(10010000,11009999)
EVENT_BLOCK_SIZE=25
EVENT_BLOCK_COUNT=240
STATIC_ASSIGNED=frozenset((*range(201,205),301,*range(401,405),*range(501,529),*range(601,603),*range(701,729),900))

@dataclass(frozen=True, slots=True)
class V2EventBlock:
    event_key: str
    ordinal: int
    start_id: int
    end_id: int
    def __post_init__(self):
        if not self.event_key.strip() or self.end_id-self.start_id+1 != EVENT_BLOCK_SIZE: raise ValueError("invalid_event_block")

@dataclass(frozen=True, slots=True)
class V2StoryQuestItemKey:
    user_id: int
    quest_id: str
    item_key: str
    def __post_init__(self):
        if self.user_id <= 0 or not self.quest_id.strip() or not self.item_key.strip(): raise ValueError("invalid_story_item_key")

@dataclass(frozen=True, slots=True)
class V2PreviewPromotion:
    preview_id: int
    permanent_id: int
    def __post_init__(self):
        if not PREVIEW_RANGE.contains(self.preview_id) or not GENERATED_RANGE.contains(self.permanent_id): raise ValueError("invalid_promotion")

def event_block(ordinal: int, event_key: str) -> V2EventBlock:
    if not 0 <= ordinal < EVENT_BLOCK_COUNT: raise ValueError("event_block_exhausted")
    start=EVENT_RANGE.start+ordinal*EVENT_BLOCK_SIZE
    return V2EventBlock(event_key,ordinal,start,start+EVENT_BLOCK_SIZE-1)

def classify_numeric_item_id(value: int) -> V2ItemIdNamespace:
    if value in STATIC_ASSIGNED:return V2ItemIdNamespace.STATIC
    if EVENT_RANGE.contains(value):return V2ItemIdNamespace.EVENT
    if GENERATED_RANGE.contains(value):return V2ItemIdNamespace.GENERATED
    if PREVIEW_RANGE.contains(value):return V2ItemIdNamespace.PREVIEW
    raise ValueError("unassigned_reserved_or_out_of_namespace")
