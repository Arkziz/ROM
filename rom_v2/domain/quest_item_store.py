from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class V2QuestItemBalanceKey:
    user_id: int
    quest_id: int
    item_key: str
    def __post_init__(self) -> None:
        if self.user_id <= 0 or self.quest_id <= 0 or not self.item_key.strip():
            raise ValueError("invalid_identity")

@dataclass(frozen=True, slots=True)
class V2QuestItemBalance:
    key: V2QuestItemBalanceKey
    quantity: int
    revision: int = 0
    def __post_init__(self) -> None:
        if self.quantity < 0 or self.revision < 0:
            raise ValueError("invalid_quantity")

@dataclass(frozen=True, slots=True)
class V2QuestItemCollection:
    key: V2QuestItemBalanceKey
    event_id: str
    quantity: int
    def __post_init__(self) -> None:
        if not self.event_id.strip() or self.quantity <= 0:
            raise ValueError("invalid_collection")

@dataclass(frozen=True, slots=True)
class V2QuestItemStoreResult:
    ok: bool
    reason: str | None = None
    balance: V2QuestItemBalance | None = None
    consumed: int = 0

@dataclass(frozen=True, slots=True)
class V2QuestItemTurnInPlan:
    key: V2QuestItemBalanceKey
    required_quantity: int
    expected_revision: int
    completion_key: str
    def __post_init__(self) -> None:
        if self.required_quantity <= 0 or self.expected_revision < 0 or not self.completion_key.strip():
            raise ValueError("invalid_turn_in_plan")
