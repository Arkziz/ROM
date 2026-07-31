"""Pure central-drop engine foundation for ROM Stage 11.

11.1.0 performs no database reads/writes and is not connected to combat. It
validates and rolls shadow configuration using injected randomness.
"""
from __future__ import annotations

from copy import deepcopy
from data.drop_tables import (
    BAG_POLICIES,
    CENTRAL_DROP_PRODUCTION_ENABLED,
    DROP_MODES,
    DROP_RULES,
    DROP_RULES_BY_ID,
    ENEMY_SIGNAL_ALIASES,
    ENEMY_TYPE_FIELDS,
    ENEMY_TYPES,
    RESOLVER_TYPES,
)

_EPSILON = 1e-9


def classify_enemy(mob):
    """Return exactly one enemy type using boss > elite > normal priority."""
    mob = mob or {}
    explicit_types = {
        str(mob.get(field, "") or "").strip().lower()
        for field in ENEMY_TYPE_FIELDS
    }
    if "boss" in explicit_types or any(bool(mob.get(key, False)) for key in ENEMY_SIGNAL_ALIASES["boss"]):
        return "boss"
    if "elite" in explicit_types or any(bool(mob.get(key, False)) for key in ENEMY_SIGNAL_ALIASES["elite"]):
        return "elite"
    return "normal"


def _is_probability(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= float(value) <= 1.0


def _validate_weights(weights, path, allow_empty=False):
    errors = []
    if not isinstance(weights, (tuple, list)):
        return [f"{path}: weights must be a tuple/list"]
    if not weights:
        return [] if allow_empty else [f"{path}: weights must not be empty"]
    total = 0.0
    values = set()
    for index, pair in enumerate(weights):
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            errors.append(f"{path}[{index}]: expected (value, weight)")
            continue
        value, weight = pair
        if value in values:
            errors.append(f"{path}: duplicate value {value!r}")
        values.add(value)
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or float(weight) < 0:
            errors.append(f"{path}[{index}]: invalid weight {weight!r}")
        else:
            total += float(weight)
    if abs(total - 1.0) > _EPSILON:
        errors.append(f"{path}: weights sum to {total}, expected 1.0")
    return errors


def validate_drop_rule(rule):
    """Return a list of schema errors for one rule."""
    errors = []
    required = (
        "rule_id", "group", "mode", "enabled", "production_enabled",
        "resolver", "enemy", "quantity", "max_per_kill", "bag_policy",
        "message_policy", "migration_stage",
    )
    for key in required:
        if key not in rule:
            errors.append(f"missing field: {key}")
    if errors:
        return errors
    prefix = str(rule["rule_id"])
    if not prefix or not prefix.replace("_", "").isalnum():
        errors.append(f"{prefix}: invalid rule_id")
    if rule["mode"] not in DROP_MODES:
        errors.append(f"{prefix}: invalid mode {rule['mode']!r}")
    if rule["resolver"] not in RESOLVER_TYPES:
        errors.append(f"{prefix}: invalid resolver {rule['resolver']!r}")
    if rule["bag_policy"] not in BAG_POLICIES:
        errors.append(f"{prefix}: invalid bag_policy {rule['bag_policy']!r}")
    if not isinstance(rule["enabled"], bool) or not isinstance(rule["production_enabled"], bool):
        errors.append(f"{prefix}: enabled flags must be bool")
    if rule["production_enabled"] and not CENTRAL_DROP_PRODUCTION_ENABLED:
        errors.append(f"{prefix}: production rule enabled while central production is disabled")
    if set(rule["enemy"]) != set(ENEMY_TYPES):
        errors.append(f"{prefix}: enemy keys must equal {ENEMY_TYPES}")
    for enemy_type, config in rule["enemy"].items():
        chance = config.get("chance")
        if chance is not None and not _is_probability(chance):
            errors.append(f"{prefix}.{enemy_type}: invalid chance {chance!r}")
        if chance is None and not any(key in config for key in ("inherits", "source", "decision_required")):
            errors.append(f"{prefix}.{enemy_type}: unresolved chance has no metadata")
    quantity = rule["quantity"]
    minimum, maximum = quantity.get("min"), quantity.get("max")
    if not isinstance(minimum, int) or minimum < 1:
        errors.append(f"{prefix}: quantity.min must be a positive integer")
    if maximum is not None and (not isinstance(maximum, int) or maximum < minimum):
        errors.append(f"{prefix}: quantity.max must be None or >= min")
    if not isinstance(rule["max_per_kill"], int) or rule["max_per_kill"] < 0:
        errors.append(f"{prefix}: max_per_kill must be a non-negative integer")
    if rule["resolver"] == "static_item" and not isinstance(rule.get("item_id"), int):
        errors.append(f"{prefix}: static_item resolver requires item_id")
    if "level_weights" in rule:
        for enemy_type in ENEMY_TYPES:
            errors.extend(_validate_weights(rule["level_weights"].get(enemy_type), f"{prefix}.level_weights.{enemy_type}"))
    if "stat_weights" in rule:
        errors.extend(_validate_weights(rule["stat_weights"], f"{prefix}.stat_weights"))
    if "item_weights" in rule:
        errors.extend(_validate_weights(rule["item_weights"], f"{prefix}.item_weights", allow_empty=not rule["enabled"]))
    return errors


def validate_drop_tables(rules=None):
    """Validate all rules and return a structured, non-throwing result."""
    selected = tuple(DROP_RULES if rules is None else rules)
    errors = []
    seen = set()
    for index, rule in enumerate(selected):
        rule_id = rule.get("rule_id", f"index_{index}") if isinstance(rule, dict) else f"index_{index}"
        if not isinstance(rule, dict):
            errors.append(f"{rule_id}: rule must be dict")
            continue
        if rule_id in seen:
            errors.append(f"duplicate rule_id: {rule_id}")
        seen.add(rule_id)
        errors.extend(f"{rule_id}: {error}" for error in validate_drop_rule(rule))
    return {"success": not errors, "errors": errors, "rule_count": len(selected)}


def resolve_enemy_config(rule, enemy_type, context=None):
    """Resolve chance metadata without inventing unresolved balance decisions."""
    if enemy_type not in ENEMY_TYPES:
        raise ValueError(f"unsupported enemy_type: {enemy_type}")
    context = context or {}
    config = deepcopy(rule["enemy"][enemy_type])
    visited = set()
    while config.get("chance") is None and config.get("inherits"):
        inherited = str(config["inherits"])
        if inherited in visited or inherited not in ENEMY_TYPES:
            raise ValueError(f"invalid inheritance in rule {rule['rule_id']}")
        visited.add(inherited)
        inherited_config = deepcopy(rule["enemy"][inherited])
        inherited_config["inherited_from"] = inherited
        config = inherited_config
    if config.get("chance") is None and config.get("source"):
        source = config["source"]
        if source == "mob.loot_chance":
            config["chance"] = float(context.get("mob", {}).get("loot_chance", 0.45))
        elif source == "min(1,mob.loot_chance+0.20)":
            config["chance"] = min(1.0, float(context.get("mob", {}).get("loot_chance", 0.45)) + 0.20)
    return config


def weighted_choice(weights, random_value):
    """Pure weighted choice using one caller-provided value in [0,1)."""
    errors = _validate_weights(weights, "weights")
    if errors:
        raise ValueError("; ".join(errors))
    point = max(0.0, min(0.999999999999, float(random_value)))
    cumulative = 0.0
    for value, weight in weights:
        cumulative += float(weight)
        if point < cumulative:
            return value
    return weights[-1][0]


def make_drop_result(rule, enemy_type, rolled, awarded=False, lost=False, reason=None, payload=None):
    """Create the canonical result contract used by later migration stages."""
    return {
        "rule_id": rule["rule_id"],
        "group": rule["group"],
        "mode": rule["mode"],
        "enemy_type": enemy_type,
        "rolled": bool(rolled),
        "awarded": bool(awarded),
        "lost": bool(lost),
        "reason": reason,
        "payload": deepcopy(payload) if payload is not None else None,
        "bag_policy": rule["bag_policy"],
        "message_policy": rule["message_policy"],
    }


def roll_drop_rule(rule, mob, random_func, context=None):
    """Pure shadow roll for one rule. No DB access and no item award."""
    enemy_type = classify_enemy(mob)
    if not rule.get("enabled", False):
        return make_drop_result(rule, enemy_type, False, reason="rule_disabled")
    config = resolve_enemy_config(rule, enemy_type, {"mob": mob, **(context or {})})
    chance = config.get("chance")
    if chance is None:
        return make_drop_result(rule, enemy_type, False, reason="balance_decision_required", payload={"config": config})
    roll = float(random_func())
    if roll >= float(chance):
        return make_drop_result(rule, enemy_type, False, reason="chance_miss", payload={"chance": chance, "roll": roll})
    payload = {"chance": chance, "roll": roll, "resolver": rule["resolver"]}
    if rule["resolver"] == "static_item":
        payload.update({"item_id": rule["item_id"], "quantity": rule["quantity"]["min"]})
    elif rule["resolver"] == "rune":
        payload["level"] = weighted_choice(rule["level_weights"][enemy_type], random_func())
        payload["stat"] = weighted_choice(rule["stat_weights"], random_func())
        payload["quantity"] = 1
    elif rule["resolver"] == "weighted_item_pool":
        payload["item_id"] = weighted_choice(rule["item_weights"], random_func())
        payload["quantity"] = rule["quantity"]["min"]
    else:
        payload["deferred_resolver"] = True
    return make_drop_result(rule, enemy_type, True, reason="shadow_roll_hit", payload=payload)


def roll_drop_group(group, mob, random_func, context=None, rules=None):
    """Pure roll of all enabled rules in a group, respecting max_per_kill."""
    selected = [
        rule for rule in (DROP_RULES if rules is None else rules)
        if rule.get("group") == group
    ]
    results = []
    hits = 0
    for rule in selected:
        if hits >= int(rule.get("max_per_kill", 1)):
            results.append(make_drop_result(rule, classify_enemy(mob), False, reason="group_limit"))
            continue
        result = roll_drop_rule(rule, mob, random_func, context=context)
        results.append(result)
        if result["rolled"]:
            hits += 1
    return results


def roll_enemy_drops(mob, random_func, context=None, rules=None):
    """Pure full-table shadow simulation; still never awards items."""
    selected = tuple(DROP_RULES if rules is None else rules)
    validation = validate_drop_tables(selected)
    if not validation["success"]:
        raise ValueError("; ".join(validation["errors"]))
    return [roll_drop_rule(rule, mob, random_func, context=context) for rule in selected]


def get_drop_rule(rule_id):
    rule = DROP_RULES_BY_ID.get(str(rule_id))
    return deepcopy(rule) if rule is not None else None


def get_central_drop_status():
    validation = validate_drop_tables()
    return {
        "schema_valid": validation["success"],
        "errors": validation["errors"],
        "rule_count": validation["rule_count"],
        "production_enabled": CENTRAL_DROP_PRODUCTION_ENABLED,
        "production_rules": [rule["rule_id"] for rule in DROP_RULES if rule.get("production_enabled")],
        "shadow_only": not CENTRAL_DROP_PRODUCTION_ENABLED,
    }

# ==============================
# ROM 11.2.0 CENTRAL RUNE MIGRATION
# ==============================

def roll_central_rune_drop(mob, random_func):
    """Production rune roll backed by the canonical central `rune` rule.

    This function is pure and consumes exactly the same random values as the
    legacy implementation: one chance roll, then level and stat only on hit.
    """
    rule = get_drop_rule("rune")
    if rule is None:
        raise RuntimeError("central rune drop rule is missing")
    if not rule.get("production_enabled", False):
        raise RuntimeError("central rune drop rule is not production-enabled")
    return roll_drop_rule(rule, mob, random_func)

# ==============================
# ROM 11.3.0 CENTRAL REFINE STONE MIGRATION
# ==============================

def roll_central_refine_stone_drop(mob, random_func):
    """Pure production roll for one Enhancement Stone (item 401).

    The legacy Refine Stone contract uses `roll <= chance`, while the rune
    contract uses `roll < chance`. Preserve the material-specific inclusive
    boundary here instead of changing the generic engine and breaking exact
    rune equivalence.
    """
    rule = get_drop_rule("refine_stone")
    if rule is None:
        raise RuntimeError("central refine_stone rule is missing")
    if not rule.get("production_enabled", False):
        raise RuntimeError("central refine_stone rule is not production-enabled")

    enemy_type = classify_enemy(mob)
    config = resolve_enemy_config(rule, enemy_type, {"mob": mob or {}})
    chance = config.get("chance")
    if chance is None:
        return make_drop_result(
            rule,
            enemy_type,
            False,
            reason="balance_decision_required",
            payload={"config": config},
        )

    roll = float(random_func())
    payload = {"chance": float(chance), "roll": roll}
    if roll > float(chance):
        return make_drop_result(
            rule,
            enemy_type,
            False,
            reason="chance_miss",
            payload=payload,
        )

    payload.update({
        "resolver": "static_item",
        "item_id": int(rule["item_id"]),
        "quantity": int(rule["quantity"]["min"]),
        "boundary": "inclusive",
    })
    return make_drop_result(
        rule,
        enemy_type,
        True,
        reason="shadow_roll_hit",
        payload=payload,
    )

# ==============================
# ROM 11.4.0 CENTRAL EQUIPMENT MIGRATION
# ==============================

def _weighted_choice_inclusive_11_4_0(weights, random_value):
    """Legacy-equivalent weighted choice using inclusive upper boundaries."""
    errors = _validate_weights(weights, "equipment_weights")
    if errors:
        raise ValueError("; ".join(errors))
    point = float(random_value)
    cumulative = 0.0
    for value, weight in weights:
        cumulative += float(weight)
        if point <= cumulative:
            return value
    return weights[-1][0]


def roll_central_equipment_drop(mob, random_func):
    """Pure equipment selection preserving legacy RNG order and boundaries.

    RNG order on a successful drop:
    1. drop chance
    2. rarity

    The class-aware probability is passed to the existing equipment creator,
    which remains the authoritative generator and consumes its own RNG exactly
    as before.
    """
    rule = get_drop_rule("equipment")
    if rule is None:
        raise RuntimeError("central equipment rule is missing")
    if not rule.get("production_enabled", False):
        raise RuntimeError("central equipment rule is not production-enabled")

    enemy_type = classify_enemy(mob)
    config = resolve_enemy_config(rule, enemy_type, {"mob": mob or {}})
    chance = config.get("chance")
    if chance is None:
        return make_drop_result(
            rule, enemy_type, False, reason="balance_decision_required",
            payload={"config": config},
        )

    roll = float(random_func())
    payload = {"chance": float(chance), "roll": roll}
    if roll > float(chance):
        return make_drop_result(
            rule, enemy_type, False, reason="chance_miss", payload=payload,
        )

    rarity = _weighted_choice_inclusive_11_4_0(
        rule["rarity_weights"][enemy_type], random_func()
    )
    payload.update({
        "resolver": "equipment",
        "rarity": rarity,
        "class_aware_chance": float(rule["class_aware_chance"][enemy_type]),
        "quantity": 1,
        "boundary": "inclusive",
    })
    return make_drop_result(
        rule, enemy_type, True, reason="shadow_roll_hit", payload=payload,
    )

