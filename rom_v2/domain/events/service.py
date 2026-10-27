"""API-ready event schedule/reward evaluation without runtime wiring."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .rewards import DirectRewardCatalog
from .schedule import EventDefinition, EventLifecycle


@dataclass(frozen=True, slots=True)
class EventEvaluation:
    event_key: str
    lifecycle: EventLifecycle
    eligible: bool
    direct_reward_item_ids: tuple[int, ...]


class EventScheduleRewardService:
    """Fail-closed deterministic evaluator for registered event definitions."""

    def __init__(
        self,
        definitions: tuple[EventDefinition, ...],
        direct_rewards: tuple[DirectRewardCatalog, ...] = (),
    ) -> None:
        definition_map: dict[str, EventDefinition] = {}
        for definition in definitions:
            if definition.event_key in definition_map:
                raise ValueError(f"duplicate_event_key::{definition.event_key}")
            definition_map[definition.event_key] = definition

        reward_map: dict[str, DirectRewardCatalog] = {}
        for catalog in direct_rewards:
            if catalog.event_key in reward_map:
                raise ValueError(f"duplicate_direct_reward_catalog::{catalog.event_key}")
            if catalog.event_key not in definition_map:
                raise ValueError(f"direct_reward_event_not_registered::{catalog.event_key}")
            reward_map[catalog.event_key] = catalog

        self._definitions = definition_map
        self._direct_rewards = reward_map

    def evaluate(self, event_key: str, instant: datetime) -> EventEvaluation:
        """Evaluate enabled/window eligibility and expose only direct rewards."""
        definition = self._definitions.get(event_key)
        if definition is None:
            raise KeyError(f"unknown_event_key::{event_key}")
        lifecycle = definition.schedule.lifecycle_at(instant, enabled=definition.enabled)
        catalog = self._direct_rewards.get(event_key)
        item_ids = catalog.item_ids if catalog is not None else ()
        return EventEvaluation(
            event_key=event_key,
            lifecycle=lifecycle,
            eligible=lifecycle is EventLifecycle.ACTIVE,
            direct_reward_item_ids=item_ids,
        )
