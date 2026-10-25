from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class V2NpcActionKind(str, Enum):
    STORY_QUEST = "story_quest"

@dataclass(frozen=True, slots=True)
class V2NpcDefinition:
    npc_id: str
    display_name: str
    location_id: str
    quest_ids: tuple[int, ...] = ()
    def __post_init__(self) -> None:
        if not self.npc_id.strip() or not self.display_name.strip() or not self.location_id.strip():
            raise ValueError("invalid_npc_definition")
        if len(set(self.quest_ids)) != len(self.quest_ids) or any(q <= 0 for q in self.quest_ids):
            raise ValueError("invalid_quest_reference")

@dataclass(frozen=True, slots=True)
class V2NpcAction:
    action_key: str
    kind: V2NpcActionKind
    quest_id: int
    expected_revision: int
    label: str

@dataclass(frozen=True, slots=True)
class V2NpcView:
    npc_id: str
    display_name: str
    location_id: str
    actions: tuple[V2NpcAction, ...]

@dataclass(frozen=True, slots=True)
class V2NpcInteractionResult:
    ok: bool
    reason: str | None = None
    view: V2NpcView | None = None
    quest_result: object | None = None

@dataclass(frozen=True, slots=True)
class V2NpcAcceptCommand:
    user_id: int
    npc_id: str
    quest_id: int
    expected_revision: int
