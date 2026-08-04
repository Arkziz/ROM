from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from .rng import SimulationRng
from .rng_adapter import inject_module_rng


class CanonicalRuleError(RuntimeError):
    pass


@dataclass(frozen=True)
class CanonicalRuleDescriptor:
    name: str
    module: str
    function: str
    deterministic: bool
    rng_injected: bool = False
    notes: str = ""


RULES: Tuple[CanonicalRuleDescriptor, ...] = (
    CanonicalRuleDescriptor("physical_crit_chance", "systems.combat_system", "get_physical_crit_chance", True),
    CanonicalRuleDescriptor("magical_crit_chance", "systems.combat_system", "get_magical_crit_chance", True),
    CanonicalRuleDescriptor("dodge_chance", "systems.combat_system", "get_dodge_chance", True),
    CanonicalRuleDescriptor("elite_modifier", "systems.combat_system", "apply_elite_modifier", True),
    CanonicalRuleDescriptor("available_mobs", "systems.combat_system", "get_available_mobs", True),
    CanonicalRuleDescriptor("player_attack", "systems.combat_system", "calculate_player_attack", True, True),
    CanonicalRuleDescriptor("mob_attack", "systems.combat_system", "calculate_mob_attack", True, True),
    CanonicalRuleDescriptor("weapon_damage", "systems.equipment_system", "calculate_weapon_damage_by_values", True),
    CanonicalRuleDescriptor("repair_cost", "systems.equipment_system", "calculate_repair_cost", True),
    CanonicalRuleDescriptor("armor_refine_hp_percent", "systems.refine_system", "get_armor_refine_hp_bonus_percent", True),
    CanonicalRuleDescriptor("weapon_refine_damage", "systems.refine_system", "apply_weapon_refine_to_damage", True),
    CanonicalRuleDescriptor("refine_success_chance", "systems.refine_system", "get_refine_success_chance", True),
    CanonicalRuleDescriptor("refine_success_roll", "systems.refine_system", "roll_refine_success", True, True),
    CanonicalRuleDescriptor("normal_equipment_rarity", "systems.reward_system", "roll_normal_equipment_rarity", True, True),
    CanonicalRuleDescriptor("elite_equipment_rarity", "systems.reward_system", "roll_elite_equipment_rarity", True, True),
    CanonicalRuleDescriptor("exp_reward", "systems.reward_system", "calculate_exp_reward", True, True),
    CanonicalRuleDescriptor("gold_reward", "systems.reward_system", "calculate_gold_reward", True, True),
)


def _import(module_name: str):
    return __import__(module_name, fromlist=["*"])


def _resolve(descriptor: CanonicalRuleDescriptor) -> Tuple[Any, Callable[..., Any]]:
    module = _import(descriptor.module)
    function = getattr(module, descriptor.function, None)
    if not callable(function):
        raise CanonicalRuleError(f"missing canonical function {descriptor.module}.{descriptor.function}")
    return module, function


def descriptor(name: str) -> CanonicalRuleDescriptor:
    for item in RULES:
        if item.name == name:
            return item
    raise CanonicalRuleError(f"unknown canonical rule: {name}")


def call_rule(name: str, *args: Any, rng: Optional[SimulationRng] = None, **kwargs: Any) -> Any:
    item = descriptor(name)
    module, function = _resolve(item)
    safe_args = deepcopy(args)
    safe_kwargs = deepcopy(kwargs)
    if item.rng_injected:
        if rng is None:
            raise CanonicalRuleError(f"rule {name} requires SimulationRng")
        with inject_module_rng(module, rng):
            return function(*safe_args, **safe_kwargs)
    if rng is not None:
        raise CanonicalRuleError(f"rule {name} does not accept RNG")
    return function(*safe_args, **safe_kwargs)


def rule_manifest() -> List[Dict[str, Any]]:
    result = []
    for item in RULES:
        module, function = _resolve(item)
        result.append({
            "name": item.name,
            "module": item.module,
            "function": item.function,
            "deterministic": item.deterministic,
            "rng_injected": item.rng_injected,
            "callable": callable(function),
        })
    return result
