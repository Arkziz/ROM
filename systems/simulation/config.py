from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class SimulationProfile:
    key: str
    start_minute: int
    end_minute: int

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("profile key is required")
        if not (0 <= self.start_minute < self.end_minute <= 24 * 60):
            raise ValueError("invalid active window")

    @property
    def active_minutes(self) -> int:
        return self.end_minute - self.start_minute


PROFILES: Dict[str, SimulationProfile] = {
    "casual": SimulationProfile("casual", 18 * 60, 21 * 60),
    "regular": SimulationProfile("regular", 17 * 60, 23 * 60),
    "hardcore": SimulationProfile("hardcore", 9 * 60, 23 * 60),
}


@dataclass(frozen=True)
class SimulationConfig:
    character_class: str
    target_level: int = 20
    profile_key: str = "regular"
    seed: int = 1
    mode: str = "EXACT"
    inventory_capacity: int = 40
    inventory_reserve_slots: int = 2
    energy_max: int = 40
    energy_regen_minutes: int = 5
    hp_potion_threshold: float = 0.30
    mp_potion_threshold: float = 0.25
    repair_threshold: int = 10
    mob_level_delta: Tuple[int, ...] = (-1, 0, 1)
    combat_policy: str = "balanced"
    pvp_enabled: bool = False
    schema_version: str = "13.1.0"

    def __post_init__(self) -> None:
        allowed_classes = {"warrior", "knight", "scout", "rogue", "mage", "priest"}
        if self.character_class not in allowed_classes:
            raise ValueError("unsupported character class")
        if self.profile_key not in PROFILES:
            raise ValueError("unsupported simulation profile")
        if self.mode not in {"EXACT", "FAST"}:
            raise ValueError("mode must be EXACT or FAST")
        if not (1 <= self.target_level <= 30):
            raise ValueError("target_level must be in range 1..30")
        if self.inventory_capacity <= 0:
            raise ValueError("inventory_capacity must be positive")
        if not (0 <= self.inventory_reserve_slots < self.inventory_capacity):
            raise ValueError("invalid inventory reserve")
        if self.energy_max <= 0 or self.energy_regen_minutes <= 0:
            raise ValueError("invalid energy configuration")
        if not (0.0 <= self.hp_potion_threshold <= 1.0):
            raise ValueError("invalid HP potion threshold")
        if not (0.0 <= self.mp_potion_threshold <= 1.0):
            raise ValueError("invalid MP potion threshold")
        if self.repair_threshold < 0:
            raise ValueError("invalid repair threshold")
        if self.pvp_enabled:
            raise ValueError("PvP simulation is deferred until production PvP exists")

    @property
    def profile(self) -> SimulationProfile:
        return PROFILES[self.profile_key]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["mob_level_delta"] = list(self.mob_level_delta)
        data["profile"] = asdict(self.profile)
        return data

    def fingerprint(self) -> str:
        raw = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return sha256(raw.encode("utf-8")).hexdigest()
