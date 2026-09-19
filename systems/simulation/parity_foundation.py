from __future__ import annotations

"""Canonical-owner foundation for deterministic Stage 18.30 simulations.

This module owns orchestration contracts only. It deliberately contains no HP,
attack, defense, progression, drop, repair, rune or refine formulas.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from importlib import import_module
from random import Random
from typing import Any, Callable, Mapping

from .clock import SimulationClock

# ROM 18.30.2 SIMULATOR PARITY FOUNDATION
SUPPORTED_CLASSES = ("warrior", "knight", "scout", "rogue", "mage", "priest")
ACTIVE_START_MINUTE = 9 * 60
ACTIVE_END_MINUTE = 23 * 60
FATIGUE_MAXIMUM = 40
FATIGUE_RECOVERY_MINUTES = 5
HUNT_HP_THRESHOLD = 0.25
POTION_HP_THRESHOLD = 0.60
REPAIR_DURABILITY_THRESHOLD = 15
REFINE_MINIMUM_SUCCESS_CHANCE = 0.50


@dataclass(frozen=True)
class SimulatorScenarioPolicy:
    active_start_minute: int = ACTIVE_START_MINUTE
    active_end_minute: int = ACTIVE_END_MINUTE
    fatigue_start: int = 0
    fatigue_per_hunt: int = 1
    fatigue_maximum: int = FATIGUE_MAXIMUM
    fatigue_recovery_minutes: int = FATIGUE_RECOVERY_MINUTES
    hunt_hp_threshold: float = HUNT_HP_THRESHOLD
    potion_hp_threshold: float = POTION_HP_THRESHOLD
    repair_durability_threshold: int = REPAIR_DURABILITY_THRESHOLD
    refine_minimum_success_chance: float = REFINE_MINIMUM_SUCCESS_CHANCE
    premium_items_enabled: bool = False
    event_encounters_enabled: bool = False
    automatic_potion_purchase_enabled: bool = False

    def validate(self) -> None:
        if not 0 <= self.active_start_minute < self.active_end_minute <= 24 * 60:
            raise ValueError("Invalid active window")
        if self.fatigue_start != 0 or self.fatigue_per_hunt != 1:
            raise ValueError("Stage 18.30 fatigue starts at 0 and increases by 1 per hunt")
        if self.fatigue_maximum != 40 or self.fatigue_recovery_minutes != 5:
            raise ValueError("Stage 18.30 fatigue contract is 40 maximum and 5-minute recovery")
        if self.hunt_hp_threshold != 0.25 or self.potion_hp_threshold != 0.60:
            raise ValueError("Stage 18.30 HP thresholds are 25% and 60%")
        if self.repair_durability_threshold != 15:
            raise ValueError("Stage 18.30 repair threshold is 15%")
        if self.refine_minimum_success_chance != 0.50:
            raise ValueError("Stage 18.30 standard refine threshold is 50%")
        if self.premium_items_enabled or self.event_encounters_enabled:
            raise ValueError("Premium items and event encounters must remain disabled")


@dataclass
class SimulatorMetrics:
    hunts: int = 0
    fatigue_waits: int = 0
    fatigue_recovered: int = 0
    wait_seconds: int = 0
    active_seconds: int = 0
    battle_seconds: int = 0
    recovery_seconds: int = 0
    other_action_seconds: int = 0
    gold_by_source: dict[str, float] = field(default_factory=dict)
    gold_by_sink: dict[str, float] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)

    def increment(self, key: str, amount: int = 1) -> None:
        self.counters[str(key)] = self.counters.get(str(key), 0) + int(amount)

    def credit_gold(self, source: str, amount: float) -> None:
        if amount < 0:
            raise ValueError("Gold credit cannot be negative")
        self.gold_by_source[str(source)] = round(self.gold_by_source.get(str(source), 0.0) + float(amount), 2)

    def debit_gold(self, sink: str, amount: float) -> None:
        if amount < 0:
            raise ValueError("Gold debit cannot be negative")
        self.gold_by_sink[str(sink)] = round(self.gold_by_sink.get(str(sink), 0.0) + float(amount), 2)

    def snapshot(self) -> dict[str, Any]:
        data = asdict(self)
        data["gold_income_total"] = round(sum(self.gold_by_source.values()), 2)
        data["gold_expense_total"] = round(sum(self.gold_by_sink.values()), 2)
        data["gold_net"] = round(data["gold_income_total"] - data["gold_expense_total"], 2)
        return data


@dataclass
class IsolatedSimulatorState:
    character_class: str
    clock: SimulationClock
    seed: int
    fatigue: int = 0
    gold: float = 0.0
    inventory: dict[int, int] = field(default_factory=dict)
    equipment: dict[str, Any] = field(default_factory=dict)
    resources: dict[str, dict[str, int]] = field(default_factory=dict)
    metrics: SimulatorMetrics = field(default_factory=SimulatorMetrics)

    def __post_init__(self) -> None:
        self.character_class = str(self.character_class).strip().lower()
        if self.character_class not in SUPPORTED_CLASSES:
            raise ValueError(f"Unsupported class: {self.character_class}")
        if self.fatigue != 0:
            raise ValueError("Stage 18.30 isolated state must start with zero fatigue")
        self.rng = Random(int(self.seed))

    def can_hunt(self, policy: SimulatorScenarioPolicy) -> bool:
        policy.validate()
        return self.fatigue < policy.fatigue_maximum

    def record_hunt(self, policy: SimulatorScenarioPolicy) -> int:
        if not self.can_hunt(policy):
            raise RuntimeError("Hunting is blocked at fatigue 40")
        self.fatigue += policy.fatigue_per_hunt
        self.metrics.hunts += 1
        return self.fatigue

    def recover_fatigue(self, policy: SimulatorScenarioPolicy, minutes: int) -> int:
        policy.validate()
        ticks = max(0, int(minutes)) // policy.fatigue_recovery_minutes
        recovered = min(self.fatigue, ticks)
        self.fatigue -= recovered
        if recovered:
            self.metrics.fatigue_waits += 1
            self.metrics.fatigue_recovered += recovered
            seconds = recovered * policy.fatigue_recovery_minutes * 60
            self.metrics.wait_seconds += seconds
            self.metrics.recovery_seconds += seconds
            self.clock.advance(seconds=seconds)
        return recovered

    def credit_gold(self, source: str, amount: float) -> None:
        self.metrics.credit_gold(source, amount)
        self.gold = round(self.gold + float(amount), 2)

    def debit_gold(self, sink: str, amount: float) -> None:
        amount = float(amount)
        if amount < 0 or amount > self.gold:
            raise ValueError("Insufficient isolated gold balance")
        self.metrics.debit_gold(sink, amount)
        self.gold = round(self.gold - amount, 2)

    def snapshot(self) -> dict[str, Any]:
        return {
            "character_class": self.character_class,
            "clock": self.clock.iso(),
            "seed": int(self.seed),
            "fatigue": int(self.fatigue),
            "gold": round(self.gold, 2),
            "inventory": dict(sorted(self.inventory.items())),
            "equipment": dict(self.equipment),
            "resources": self.resources,
            "metrics": self.metrics.snapshot(),
        }


@dataclass(frozen=True)
class CanonicalOwnerSpec:
    key: str
    module: str
    attribute: str


CANONICAL_OWNER_SPECS = (
    CanonicalOwnerSpec("progression", "data.player_progression", "apply_exp_award"),
    CanonicalOwnerSpec("max_hp", "data.player_hp", "calculate_base_max_hp"),
    CanonicalOwnerSpec("physical_crit", "data.player_combat_chances", "calculate_physical_crit_chance"),
    CanonicalOwnerSpec("magical_crit", "data.player_combat_chances", "calculate_magical_crit_chance"),
    CanonicalOwnerSpec("dodge", "data.player_combat_chances", "calculate_dodge_chance"),
    CanonicalOwnerSpec("defense", "data.defense_policy", "calculate_total_defense"),
    CanonicalOwnerSpec("repair", "db_modules.equipment", "calculate_repair_cost"),
    CanonicalOwnerSpec("rune_definition", "data.runes", "get_rune_definition"),
)


class CanonicalOwnerResolver:
    def __init__(self, specs: tuple[CanonicalOwnerSpec, ...] = CANONICAL_OWNER_SPECS):
        self._specs = {spec.key: spec for spec in specs}
        self._resolved: dict[str, Callable[..., Any]] = {}

    def resolve(self, key: str) -> Callable[..., Any]:
        normalized = str(key).strip()
        if normalized in self._resolved:
            return self._resolved[normalized]
        spec = self._specs.get(normalized)
        if spec is None:
            raise KeyError(f"Unknown canonical owner: {normalized}")
        module = import_module(spec.module)
        owner = getattr(module, spec.attribute, None)
        if not callable(owner):
            raise RuntimeError(f"Canonical owner is not callable: {spec.module}.{spec.attribute}")
        self._resolved[normalized] = owner
        return owner

    def validate_all(self) -> Mapping[str, str]:
        validated: dict[str, str] = {}
        for key, spec in self._specs.items():
            self.resolve(key)
            validated[key] = f"{spec.module}.{spec.attribute}"
        return validated


def build_isolated_state(character_class: str, seed: int, clock: SimulationClock | None = None) -> IsolatedSimulatorState:
    return IsolatedSimulatorState(
        character_class=character_class,
        seed=int(seed),
        clock=clock if clock is not None else SimulationClock.at_start(),
    )


def validate_parity_foundation() -> dict[str, Any]:
    policy = SimulatorScenarioPolicy()
    policy.validate()
    owners = CanonicalOwnerResolver().validate_all()
    first = build_isolated_state("scout", 180302)
    second = build_isolated_state("scout", 180302)
    deterministic = [first.rng.random() for _ in range(5)] == [second.rng.random() for _ in range(5)]
    if not deterministic:
        raise RuntimeError("Deterministic RNG contract failed")
    for _ in range(40):
        first.record_hunt(policy)
    if first.can_hunt(policy):
        raise RuntimeError("Fatigue 40 must block hunting")
    first.recover_fatigue(policy, 5)
    if first.fatigue != 39 or not first.can_hunt(policy):
        raise RuntimeError("Fatigue recovery must restore hunting at 39")
    first.credit_gold("mobs", 10.0)
    first.debit_gold("repair", 2.5)
    snapshot = first.snapshot()
    if snapshot["gold"] != 7.5 or snapshot["metrics"]["gold_net"] != 7.5:
        raise RuntimeError("Economic ledger invariant failed")
    return {
        "status": "PASS",
        "policy": asdict(policy),
        "canonical_owners": dict(owners),
        "deterministic_rng": deterministic,
        "fatigue_after_recovery": first.fatigue,
        "snapshot": snapshot,
    }
