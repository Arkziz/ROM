"""Direct event reward catalog.

V1 parity proves that test_event_2026 has no direct scheduled/completion reward.
Drops and event-shop offers belong to separate systems and are intentionally not
represented by this catalog.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class DirectRewardCatalog:
    """Immutable direct-reward item identifiers for one event."""

    event_key: str
    item_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        key = self.event_key.strip()
        if not key:
            raise ValueError("event_key_must_not_be_empty")
        if len(set(self.item_ids)) != len(self.item_ids):
            raise ValueError("duplicate_direct_reward_item_id")
        if any(not isinstance(item_id, int) or isinstance(item_id, bool) or item_id <= 0 for item_id in self.item_ids):
            raise ValueError("direct_reward_item_ids_must_be_positive_integers")
        object.__setattr__(self, "event_key", key)

    @property
    def is_empty(self) -> bool:
        return not self.item_ids


TEST_EVENT_2026_DIRECT_REWARDS: Final[DirectRewardCatalog] = DirectRewardCatalog(
    event_key="test_event_2026",
    item_ids=(),
)
