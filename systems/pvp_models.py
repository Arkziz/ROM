from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class PvpActionIntent:
    user_id: int
    action_type: str
    skill_key: str | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class PvpActorState:
    user_id: int
    class_key: str
    max_hp: int
    hp: int
    max_mp: int = 0
    mp: int = 0
    resource_type: str = "rage"
    resource: int = 0
    combo: int = 0
    physical_attack: float = 0.0
    magical_attack: float = 0.0
    physical_defense: float = 0.0
    magical_defense: float = 0.0
    weapon_physical_min: float = 0.0
    weapon_physical_max: float = 0.0
    weapon_magical_min: float = 0.0
    weapon_magical_max: float = 0.0
    physical_crit_chance: float = 5.0
    magical_crit_chance: float = 5.0
    dodge_chance: float = 5.0
    level: int = 1
    cooldowns: dict[str, int] = field(default_factory=dict)
    effects: dict[str, dict[str, Any]] = field(default_factory=dict)
    consecutive_afk: int = 0
    stunned_next: bool = False

    def clone(self) -> "PvpActorState":
        return PvpActorState.from_dict(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id, "class_key": self.class_key,
            "max_hp": self.max_hp, "hp": self.hp, "max_mp": self.max_mp, "mp": self.mp,
            "resource_type": self.resource_type, "resource": self.resource, "combo": self.combo,
            "physical_attack": self.physical_attack, "magical_attack": self.magical_attack,
            "physical_defense": self.physical_defense, "magical_defense": self.magical_defense,
            "weapon_physical_min": self.weapon_physical_min, "weapon_physical_max": self.weapon_physical_max,
            "weapon_magical_min": self.weapon_magical_min, "weapon_magical_max": self.weapon_magical_max,
            "physical_crit_chance": self.physical_crit_chance,
            "magical_crit_chance": self.magical_crit_chance,
            "dodge_chance": self.dodge_chance, "level": self.level,
            "cooldowns": dict(self.cooldowns),
            "effects": {key: dict(value) for key, value in self.effects.items()},
            "consecutive_afk": self.consecutive_afk, "stunned_next": self.stunned_next,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PvpActorState":
        fields = cls.__dataclass_fields__
        return cls(**{key: value[key] for key in fields if key in value})


@dataclass(frozen=True)
class PvpActionOutcome:
    user_id: int
    action_type: str
    skill_key: str | None
    valid: bool
    reason: str
    damage: int = 0
    healing: int = 0
    critical: bool = False
    dodged: bool = False
    resource_spent: int = 0
    resource_gained: int = 0
    combo_spent: int = 0
    combo_gained: int = 0
    applied_effects: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class PvpRoundResult:
    round_number: int
    revision: int
    actor_a: Mapping[str, Any]
    actor_b: Mapping[str, Any]
    outcomes: tuple[PvpActionOutcome, PvpActionOutcome]
    events: tuple[dict[str, Any], ...]
    terminal: bool
    winner_id: int | None
    result_reason: str | None
