from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

@dataclass
class BattleActor:
    name: str
    level: int
    hp: int
    max_hp: int
    attack: int
    magic_attack: int
    pdef: int
    mdef: int
    dex: int
    wis: int
    sta: int
    attack_type: str = "physical"
    weapon_min_damage: int = 0
    weapon_max_damage: int = 0
    resource_type: str = ""
    resource: int = 0
    max_resource: int = 0
    combo: int = 0
    max_combo: int = 3
    cooldowns: Dict[str, int] = field(default_factory=dict)
    effects: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @property
    def alive(self) -> bool:
        return self.hp > 0

@dataclass
class BattleAction:
    turn: int
    actor: str
    action: str
    damage: int = 0
    healing: int = 0
    critical: bool = False
    dodged: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BattleResult:
    battle_id: str
    seed: int
    battle_type: str
    player_class: str
    winner: str
    turns: int
    player_hp: int
    player_max_hp: int
    mob_hp: int
    mob_max_hp: int
    actions: List[BattleAction]
    metrics: Dict[str, Any]
    terminal_reason: str

    def to_dict(self):
        return asdict(self)
