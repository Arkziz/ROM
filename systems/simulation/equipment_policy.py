from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .models import SimulationEquipment, SimulationInventory, SimulationInventoryItem

ARMOR_COMPATIBILITY = {
    "warrior": {"mail", "кольчуга"},
    "knight": {"plate", "лати"},
    "scout": {"leather", "medium", "шкіра"},
    "rogue": {"leather", "medium", "шкіра"},
    "mage": {"cloth", "light", "тканина"},
    "priest": {"cloth", "light", "тканина"},
}

CLASS_WEIGHTS = {
    "warrior": {"str": 1.00, "sta": 0.70, "dex": 0.35, "wis": 0.10, "int": 0.00, "pdef": 0.55, "mdef": 0.25, "physical_damage": 1.00, "magical_damage": 0.00},
    "knight": {"str": 0.55, "sta": 1.00, "dex": 0.15, "wis": 0.25, "int": 0.00, "pdef": 0.90, "mdef": 0.50, "physical_damage": 0.55, "magical_damage": 0.00},
    "scout": {"str": 0.20, "sta": 0.35, "dex": 1.00, "wis": 0.10, "int": 0.00, "pdef": 0.35, "mdef": 0.20, "physical_damage": 1.00, "magical_damage": 0.00},
    "rogue": {"str": 0.35, "sta": 0.30, "dex": 1.00, "wis": 0.05, "int": 0.00, "pdef": 0.30, "mdef": 0.15, "physical_damage": 1.00, "magical_damage": 0.00},
    "mage": {"str": 0.00, "sta": 0.35, "dex": 0.05, "wis": 0.65, "int": 1.00, "pdef": 0.20, "mdef": 0.40, "physical_damage": 0.00, "magical_damage": 1.00},
    "priest": {"str": 0.00, "sta": 0.45, "dex": 0.05, "wis": 1.00, "int": 0.70, "pdef": 0.25, "mdef": 0.55, "physical_damage": 0.00, "magical_damage": 0.75},
}

RARITY_TIE_BREAK = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3}
ARMOR_SLOTS = {"helmet", "shoulders", "chest", "gloves", "legs", "boots"}

@dataclass(frozen=True)
class EquipmentScore:
    item_id: int
    simulation_item_id: int
    score: float
    compatible: bool
    reasons: Tuple[str, ...] = ()

@dataclass(frozen=True)
class EquipmentDecision:
    action: str
    candidate_id: int
    slot_key: str
    candidate_score: float
    equipped_score: float
    delta: float
    reason: str
    replaced_ids: Tuple[int, ...] = ()


def _norm(value: object) -> str:
    return str(value or "").strip().lower()


def is_class_compatible(character_class: str, item: SimulationInventoryItem) -> bool:
    character_class = _norm(character_class)
    if character_class not in CLASS_WEIGHTS:
        raise ValueError(f"unsupported class: {character_class}")
    allowed = item.stats.get("allowed_classes")
    if allowed:
        values = {_norm(value) for value in allowed}
        if character_class not in values:
            return False
    if item.slot_key in ARMOR_SLOTS and item.armor_type:
        return _norm(item.armor_type) in ARMOR_COMPATIBILITY[character_class]
    return True


def _damage_value(item: SimulationInventoryItem, magical: bool) -> float:
    stats = item.stats
    if magical:
        low = float(stats.get("weapon_min_magic_damage", stats.get("magic_min_damage", 0)) or 0)
        high = float(stats.get("weapon_max_magic_damage", stats.get("magic_max_damage", low)) or low)
    else:
        low = float(stats.get("weapon_min_damage", stats.get("min_damage", 0)) or 0)
        high = float(stats.get("weapon_max_damage", stats.get("max_damage", low)) or low)
    return (low + high) / 2.0


def score_item(character_class: str, item: SimulationInventoryItem) -> EquipmentScore:
    if not item.is_equipment:
        return EquipmentScore(item.item_id, item.simulation_item_id, float("-inf"), False, ("not_equipment",))
    if not is_class_compatible(character_class, item):
        return EquipmentScore(item.item_id, item.simulation_item_id, float("-inf"), False, ("class_incompatible",))
    weights = CLASS_WEIGHTS[_norm(character_class)]
    stats = item.stats
    score = 0.0
    for key in ("str", "dex", "int", "wis", "sta", "pdef", "mdef"):
        score += float(stats.get(key, stats.get(f"bonus_{key}", 0)) or 0) * weights[key]
    score += _damage_value(item, False) * weights["physical_damage"]
    score += _damage_value(item, True) * weights["magical_damage"]
    score += float(item.refine_level) * 1.25
    score += sum(float(getattr(rune, "bonus_value", 0) or 0) for rune in item.runes)
    score += float(stats.get("filled_socket_value", 0) or 0)
    # Empty sockets have limited potential value and never beat real stats by themselves.
    score += float(stats.get("empty_rune_slots", 0) or 0) * 0.35
    if item.durability <= 0:
        score = 0.0
    return EquipmentScore(item.item_id, item.simulation_item_id, round(score, 6), True, ())


def _by_id(inventory: SimulationInventory) -> Dict[int, SimulationInventoryItem]:
    return {item.simulation_item_id: item for item in inventory.items}


def equipped_set_score(character_class: str, ids: Iterable[int], inventory: SimulationInventory) -> float:
    items = _by_id(inventory)
    return round(sum(score_item(character_class, items[item_id]).score for item_id in ids if item_id in items), 6)


def evaluate_candidate(character_class: str, candidate: SimulationInventoryItem, inventory: SimulationInventory, equipment: SimulationEquipment) -> EquipmentDecision:
    scored = score_item(character_class, candidate)
    if not scored.compatible:
        return EquipmentDecision("sell", candidate.simulation_item_id, candidate.slot_key, scored.score, 0.0, 0.0, "class_incompatible")
    if not candidate.slot_key:
        return EquipmentDecision("sell", candidate.simulation_item_id, "", scored.score, 0.0, 0.0, "no_equipment_slot")
    items = _by_id(inventory)
    current_ids: List[int] = []
    if candidate.slot_key == "main_hand" and int(candidate.weapon_hands or 1) == 2:
        current_ids = [value for value in (equipment.slots.get("main_hand"), equipment.slots.get("off_hand")) if value]
    elif candidate.slot_key == "main_hand":
        current_ids = [value for value in (equipment.slots.get("main_hand"),) if value]
    else:
        current_ids = [value for value in (equipment.slots.get(candidate.slot_key),) if value]
    current_score = equipped_set_score(character_class, current_ids, inventory)
    delta = round(scored.score - current_score, 6)
    if not current_ids:
        return EquipmentDecision("equip", candidate.simulation_item_id, candidate.slot_key, scored.score, 0.0, scored.score, "empty_slot")
    if delta > 0:
        return EquipmentDecision("equip", candidate.simulation_item_id, candidate.slot_key, scored.score, current_score, delta, "higher_effective_score", tuple(current_ids))
    if delta == 0:
        old_rarity = max((RARITY_TIE_BREAK.get(items[value].rarity, 0) for value in current_ids if value in items), default=0)
        if RARITY_TIE_BREAK.get(candidate.rarity, 0) > old_rarity:
            return EquipmentDecision("equip", candidate.simulation_item_id, candidate.slot_key, scored.score, current_score, 0.0, "rarity_tie_break", tuple(current_ids))
    return EquipmentDecision("sell", candidate.simulation_item_id, candidate.slot_key, scored.score, current_score, delta, "not_an_upgrade", tuple(current_ids))
