from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Sequence

@dataclass(frozen=True)
class BehaviorDecision:
    action: str
    reason: str
    payload: Dict[str, Any]

@dataclass(frozen=True)
class BehaviorPolicy:
    hp_potion_threshold: float = 0.40
    mp_potion_threshold: float = 0.25
    repair_threshold: int = 15
    reserve_slots: int = 2
    style: str = "balanced"

    def choose_potion(self, hp: int, max_hp: int, mp: int, max_mp: int, mana_class: bool, hp_potions: Sequence[Dict[str, Any]], mp_potions: Sequence[Dict[str, Any]]) -> Optional[BehaviorDecision]:
        if max_hp > 0 and hp / max_hp < self.hp_potion_threshold and hp_potions:
            missing = max_hp - hp
            potion = min(hp_potions, key=lambda item: (max(0, int(item.get("restore", 0)) - missing), int(item.get("restore", 0))))
            return BehaviorDecision("use_hp_potion", "hp_below_40_percent", dict(potion))
        if mana_class and max_mp > 0 and mp / max_mp < self.mp_potion_threshold and mp_potions:
            missing = max_mp - mp
            potion = min(mp_potions, key=lambda item: (max(0, int(item.get("restore", 0)) - missing), int(item.get("restore", 0))))
            return BehaviorDecision("use_mp_potion", "mp_below_25_percent", dict(potion))
        return None

    def maintenance(self, durability_values: Iterable[int], free_slots: int) -> Optional[BehaviorDecision]:
        values = list(durability_values)
        if values and min(values) <= self.repair_threshold:
            return BehaviorDecision("visit_city", "equipped_durability_at_or_below_15", {"min_durability": min(values)})
        if free_slots <= self.reserve_slots:
            return BehaviorDecision("visit_city", "inventory_reserve_reached", {"free_slots": free_slots})
        return None

    def select_mob(self, player_level: int, mobs: Sequence[Dict[str, Any]], contract_target: str = "") -> Optional[Dict[str, Any]]:
        allowed = [mob for mob in mobs if abs(int(mob.get("level", 1)) - int(player_level)) <= 1]
        if contract_target:
            target = next((mob for mob in allowed if str(mob.get("name", "")) == contract_target), None)
            if target:
                return target
        if not allowed:
            return None
        # Balanced policy prefers equal level, then lower risk, then +1.
        return min(allowed, key=lambda mob: (abs(int(mob.get("level", 1)) - player_level), int(mob.get("level", 1)) > player_level, str(mob.get("name", ""))))
