"""Pure deterministic V2 central loot planner.

The planner owns no persistence, inventory mutation, presentation, generated
item identity, event loot, story quest items, Premium rules, or runtime wiring.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Protocol, Sequence

EnemyClass = Literal["normal", "elite", "boss"]
LootKind = Literal["item", "equipment_request"]

class CentralLootConfigurationError(ValueError):
    """Raised before rolling when a rule set violates the planner contract."""

class LootRandomSource(Protocol):
    """Explicit RNG boundary; implementations must preserve call ordering."""
    def random(self) -> float: ...

@dataclass(frozen=True, slots=True)
class LootCandidate:
    key: str
    weight: float = 1.0
    quantity: int = 1
    kind: LootKind = "item"

@dataclass(frozen=True, slots=True)
class LootRule:
    rule_key: str
    source_group: str
    chances: tuple[tuple[EnemyClass, float], ...]
    candidates: tuple[LootCandidate, ...]
    enabled: bool = True

    def chance_for(self, enemy_class: EnemyClass) -> float:
        return dict(self.chances).get(enemy_class, 0.0)

@dataclass(frozen=True, slots=True)
class LootGroup:
    group_key: str
    rules: tuple[LootRule, ...]
    max_per_kill: int | None = None

@dataclass(frozen=True, slots=True)
class CentralLootCommand:
    source_group: str
    key: str
    quantity: int
    kind: LootKind

@dataclass(frozen=True, slots=True)
class CentralLootEquipmentRequest:
    source_group: str
    request_key: str
    player_class: str
    enemy_class: EnemyClass
    enemy_level: int

@dataclass(frozen=True, slots=True)
class LootRollTrace:
    group_key: str
    rule_key: str
    chance: float
    roll: float | None
    outcome: Literal["disabled", "miss", "selected", "group_limit"]
    selected_key: str | None = None
    selection_roll: float | None = None

@dataclass(frozen=True, slots=True)
class CentralLootResult:
    immutable_loot_commands: tuple[CentralLootCommand, ...]
    equipment_generation_requests: tuple[CentralLootEquipmentRequest, ...]
    roll_trace: tuple[LootRollTrace, ...]

class CentralLootPlanner:
    """Roll source-ordered groups and rules without side effects or rerolls."""
    def plan(self, *, enemy_class: EnemyClass, enemy_level: int,
             player_class: str, location_key: str,
             rules: Sequence[LootGroup], rng: LootRandomSource) -> CentralLootResult:
        self._validate(enemy_class, enemy_level, player_class, location_key, rules)
        commands=[]; equipment=[]; trace=[]
        for group in rules:
            selected_count=0
            for rule in group.rules:
                if group.max_per_kill is not None and selected_count >= group.max_per_kill:
                    trace.append(LootRollTrace(group.group_key,rule.rule_key,rule.chance_for(enemy_class),None,"group_limit"));continue
                if not rule.enabled:
                    trace.append(LootRollTrace(group.group_key,rule.rule_key,rule.chance_for(enemy_class),None,"disabled"));continue
                chance=rule.chance_for(enemy_class); roll=float(rng.random())
                if not 0.0 <= roll < 1.0:raise CentralLootConfigurationError("rng_random_out_of_range")
                if roll >= chance:
                    trace.append(LootRollTrace(group.group_key,rule.rule_key,chance,roll,"miss"));continue
                candidate,selection_roll=self._weighted(rule.candidates,rng)
                selected_count+=1
                if candidate.kind=="equipment_request":
                    equipment.append(CentralLootEquipmentRequest(rule.source_group,candidate.key,player_class,enemy_class,enemy_level))
                else:
                    commands.append(CentralLootCommand(rule.source_group,candidate.key,candidate.quantity,candidate.kind))
                trace.append(LootRollTrace(group.group_key,rule.rule_key,chance,roll,"selected",candidate.key,selection_roll))
        return CentralLootResult(tuple(commands),tuple(equipment),tuple(trace))

    @staticmethod
    def _weighted(candidates: Sequence[LootCandidate], rng: LootRandomSource) -> tuple[LootCandidate, float | None]:
        if len(candidates)==1:return candidates[0],None
        total=sum(float(x.weight) for x in candidates); draw=float(rng.random())
        if not 0.0 <= draw < 1.0:raise CentralLootConfigurationError("rng_random_out_of_range")
        point=draw*total; upto=0.0
        for candidate in candidates:
            upto+=float(candidate.weight)
            if point < upto:return candidate,draw
        return candidates[-1],draw

    @staticmethod
    def _validate(enemy_class, enemy_level, player_class, location_key, groups):
        if enemy_class not in ("normal","elite","boss"):raise CentralLootConfigurationError("invalid_enemy_class")
        if int(enemy_level)<=0:raise CentralLootConfigurationError("positive_enemy_level_required")
        if not player_class.strip() or not location_key.strip():raise CentralLootConfigurationError("player_class_and_location_required")
        group_keys=set();rule_keys=set()
        for group in groups:
            if not group.group_key or group.group_key in group_keys:raise CentralLootConfigurationError("invalid_or_duplicate_group_key")
            group_keys.add(group.group_key)
            if group.max_per_kill is not None and group.max_per_kill<0:raise CentralLootConfigurationError("negative_group_limit")
            for rule in group.rules:
                if not rule.rule_key or rule.rule_key in rule_keys:raise CentralLootConfigurationError("invalid_or_duplicate_rule_key")
                rule_keys.add(rule.rule_key)
                chances=dict(rule.chances)
                if len(chances)!=len(rule.chances) or any(k not in ("normal","elite","boss") or not 0.0<=float(v)<=1.0 for k,v in rule.chances):raise CentralLootConfigurationError("invalid_chance_matrix")
                if not rule.candidates:raise CentralLootConfigurationError("empty_candidates")
                if any(not c.key or c.quantity<=0 or c.weight<=0 or c.kind not in ("item","equipment_request") for c in rule.candidates):raise CentralLootConfigurationError("invalid_candidate")
