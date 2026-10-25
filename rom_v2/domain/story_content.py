from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

@dataclass(frozen=True, slots=True)
class V2StoryQuestContentRecord:
    quest_id: str
    number: int
    title: str
    quest_type: str
    location_id: str
    unlock_level: int
    previous_quest_id: str | None
    giver_npc_id: str | None
    turn_in_npc_id: str | None
    target_quantity: int
    description: str
    objective_text: str
    acceptance_text: str
    completion_text: str
    reward_exp: int
    reward_gold: float
    metadata: Mapping[str, Any]
    def __post_init__(self) -> None:
        if not self.quest_id.strip() or not (1 <= self.number <= 100): raise ValueError("invalid_quest_identity")
        if not self.title.strip() or not self.quest_type.strip(): raise ValueError("invalid_quest_text")
        if not self.location_id.strip() or self.unlock_level <= 0 or self.target_quantity <= 0: raise ValueError("invalid_quest_contract")
        if self.giver_npc_id is not None and not self.giver_npc_id.strip(): raise ValueError("invalid_giver_npc_reference")
        if self.turn_in_npc_id is not None and not self.turn_in_npc_id.strip(): raise ValueError("invalid_turn_in_npc_reference")
        if self.giver_npc_id is None and self.turn_in_npc_id is None: raise ValueError("missing_npc_reference")
        if self.reward_exp < 0 or self.reward_gold < 0: raise ValueError("invalid_reward")
        object.__setattr__(self,"metadata",MappingProxyType(dict(self.metadata)))
