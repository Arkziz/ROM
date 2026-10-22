"""Pure application API for deterministic post-combat hook dispatch.

Reward settlement must already be committed. This module owns no SQLite,
runtime, Telegram, notifications, or reward mutation.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Sequence

CANONICAL_CONSUMER_ORDER = (
    "story_region_kill", "story_boss_completion", "story_item_drop",
    "daily_quest", "guild_contract", "event_statistics", "durability",
)

class PostCombatHookContractError(ValueError):
    """Raised before mutation when an event or consumer plan is invalid."""

@dataclass(frozen=True, slots=True)
class SettledVictoryEvent:
    operation_key: str
    battle_id: str
    actor_id: int
    enemy_key: str
    enemy_class: str
    enemy_level: int
    location_key: str
    settlement_status: str
    exp_awarded: int
    combat_gold_awarded: str
    loot_summary_keys: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class PostCombatConsumerResult:
    consumer_key: str
    status: str

@dataclass(frozen=True, slots=True)
class PostCombatDispatchResult:
    operation_key: str
    consumer_results: tuple[PostCombatConsumerResult, ...]
    commit_count: int

class PostCombatConsumerPort(Protocol):
    consumer_key: str
    def consume(self, event: SettledVictoryEvent) -> None: ...

class PostCombatHooksUnitOfWorkPort(Protocol):
    def is_consumer_complete(self, operation_key: str, consumer_key: str) -> bool: ...
    def mark_consumer_complete(self, operation_key: str, consumer_key: str) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...

class PostCombatHookCoordinator:
    """Run canonical durable consumers exactly once with one hook commit."""
    def dispatch(self, *, event: SettledVictoryEvent,
                 consumers: Sequence[PostCombatConsumerPort],
                 unit_of_work: PostCombatHooksUnitOfWorkPort) -> PostCombatDispatchResult:
        self._validate_event(event)
        by_key={consumer.consumer_key:consumer for consumer in consumers}
        if len(by_key)!=len(consumers):raise PostCombatHookContractError("duplicate_consumer_key")
        unknown=set(by_key)-set(CANONICAL_CONSUMER_ORDER)
        if unknown:raise PostCombatHookContractError(f"unknown_consumer_keys:{sorted(unknown)}")
        results=[]
        try:
            for key in CANONICAL_CONSUMER_ORDER:
                consumer=by_key.get(key)
                if consumer is None:continue
                if unit_of_work.is_consumer_complete(event.operation_key,key):
                    results.append(PostCombatConsumerResult(key,"already_complete"));continue
                consumer.consume(event)
                unit_of_work.mark_consumer_complete(event.operation_key,key)
                results.append(PostCombatConsumerResult(key,"applied"))
            unit_of_work.commit()
        except Exception:
            unit_of_work.rollback()
            raise
        return PostCombatDispatchResult(event.operation_key,tuple(results),1)

    @staticmethod
    def _validate_event(event: SettledVictoryEvent) -> None:
        if not event.operation_key.strip() or not event.battle_id.strip():raise PostCombatHookContractError("stable_keys_required")
        if event.actor_id<=0 or event.enemy_level<=0:raise PostCombatHookContractError("positive_actor_and_enemy_level_required")
        if event.enemy_class not in ("normal","elite","boss"):raise PostCombatHookContractError("invalid_enemy_class")
        if event.settlement_status!="committed":raise PostCombatHookContractError("settlement_must_be_committed")
        if event.exp_awarded<0:raise PostCombatHookContractError("negative_exp_summary")
        if not event.enemy_key.strip() or not event.location_key.strip():raise PostCombatHookContractError("enemy_and_location_required")
