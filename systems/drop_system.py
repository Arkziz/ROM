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
        item_weights = rule["item_weights"]
        if isinstance(item_weights, dict):
            if set(item_weights) != set(ENEMY_TYPES):
                errors.append(f"{prefix}.item_weights: enemy keys must equal {ENEMY_TYPES}")
            for enemy_type in ENEMY_TYPES:
                errors.extend(_validate_weights(
                    item_weights.get(enemy_type),
                    f"{prefix}.item_weights.{enemy_type}",
                    allow_empty=not rule["enabled"],
                ))
        else:
            errors.extend(_validate_weights(
                item_weights, f"{prefix}.item_weights",
                allow_empty=not rule["enabled"],
            ))
    return errors


def _validate_drop_tables_schema_11_10_0(rules=None):
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
        item_weights = rule["item_weights"]
        if isinstance(item_weights, dict):
            item_weights = item_weights[enemy_type]
        payload["item_id"] = weighted_choice(item_weights, random_func())
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

# ==============================
# ROM 11.5.0 CENTRAL TROPHY MIGRATION
# ==============================

def resolve_central_trophy_chance(mob):
    """Resolve the legacy trophy chance through the canonical trophy rule.

    The pre-Stage-11 runtime adds +20 percentage points only when `is_elite`
    is truthy. Bosses had no independent trophy balance. Preserve that exact
    behavior during migration, while recording the boss path explicitly.
    """
    rule = get_drop_rule("trophy")
    if rule is None:
        raise RuntimeError("central trophy rule is missing")
    if not rule.get("production_enabled", False):
        raise RuntimeError("central trophy rule is not production-enabled")

    enemy_type = classify_enemy(mob)
    base_chance = float((mob or {}).get("loot_chance", 0.45))
    elite_bonus = 0.20 if bool((mob or {}).get("is_elite", False)) else 0.0
    chance = min(1.0, base_chance + elite_bonus)
    return {
        "enemy_type": enemy_type,
        "chance": chance,
        "base_chance": base_chance,
        "elite_flag_bonus": elite_bonus,
        "boss_policy": "legacy_elite_flag_compatibility" if enemy_type == "boss" else None,
    }


def roll_central_trophy_simple(mob, random_func, choice_func):
    """Pure legacy-equivalent roll for trash_item/loot_item/simple pools."""
    rule = get_drop_rule("trophy")
    possible_items = []
    if "trash_item_id" in mob:
        possible_items.append(mob["trash_item_id"])
    if "loot_item_id" in mob:
        possible_items.append(mob["loot_item_id"])
    if "trash_items" in mob and isinstance(mob["trash_items"], list):
        possible_items.extend(mob["trash_items"])
    if "trash_drops" in mob and isinstance(mob["trash_drops"], list):
        possible_items.extend(mob["trash_drops"])

    enemy_type = classify_enemy(mob)
    if not possible_items:
        return make_drop_result(rule, enemy_type, False, reason="empty_trophy_pool")

    config = resolve_central_trophy_chance(mob)
    roll = float(random_func())
    payload = {
        "chance": config["chance"],
        "roll": roll,
        "base_chance": config["base_chance"],
        "elite_flag_bonus": config["elite_flag_bonus"],
        "boss_policy": config["boss_policy"],
    }
    if roll > config["chance"]:
        return make_drop_result(
            rule, enemy_type, False, reason="chance_miss", payload=payload,
        )

    payload.update({
        "resolver": "mob_trophy",
        "item_id": int(choice_func(possible_items)),
        "quantity": 1,
        "pool": tuple(int(item_id) for item_id in possible_items),
        "boundary": "inclusive",
    })
    return make_drop_result(
        rule, enemy_type, True, reason="shadow_roll_hit", payload=payload,
    )


def roll_central_trophy_table_entry(loot, random_func):
    """Pure chance roll for one legacy `loot_table`/`loot` entry."""
    rule = get_drop_rule("trophy")
    chance = float((loot or {}).get("chance", 0) or 0)
    roll = float(random_func())
    payload = {
        "chance": chance,
        "roll": roll,
        "item_id": (loot or {}).get("item_id"),
        "boundary": "inclusive",
        "resolver": "mob_trophy",
    }
    if roll > chance:
        return make_drop_result(
            rule, "normal", False, reason="chance_miss", payload=payload,
        )
    return make_drop_result(
        rule, "normal", True, reason="shadow_roll_hit", payload=payload,
    )

# ==============================
# ROM 11.6.0 CENTRAL POTION DROP
# ==============================

def roll_central_potion_drop(mob, random_func):
    """Roll at most one potion using one group roll plus one weighted roll."""
    rule = get_drop_rule("potion")
    if rule is None:
        raise RuntimeError("central potion rule is missing")
    if not rule.get("production_enabled", False):
        raise RuntimeError("central potion rule is not production-enabled")

    enemy_type = classify_enemy(mob)
    chance = float(rule["enemy"][enemy_type]["chance"])
    roll = float(random_func())
    payload = {"chance": chance, "roll": roll}
    if roll > chance:
        return make_drop_result(
            rule, enemy_type, False, reason="chance_miss", payload=payload,
        )

    item_id = _weighted_choice_inclusive_11_4_0(
        rule["item_weights"][enemy_type], random_func()
    )
    payload.update({
        "resolver": "weighted_item_pool",
        "item_id": int(item_id),
        "quantity": 1,
        "boundary": "inclusive",
        "exclusive_group": True,
    })
    return make_drop_result(
        rule, enemy_type, True, reason="shadow_roll_hit", payload=payload,
    )

# ==============================
# ROM 11.7.0 SPECIAL MATERIAL POLICY GUARD
# ==============================

def validate_special_material_drop_policy(rules=None):
    """Return errors if a protected special item can enter enemy-drop runtime."""
    from data.drop_tables import (
        SPECIAL_MATERIAL_MOB_DROP_DENYLIST,
        SPECIAL_MATERIAL_SOURCE_POLICY,
    )

    selected = tuple(DROP_RULES if rules is None else rules)
    errors = []
    by_id = {rule.get("rule_id"): rule for rule in selected if isinstance(rule, dict)}

    for item_id, policy in SPECIAL_MATERIAL_SOURCE_POLICY.items():
        rule_id = policy["rule_id"]
        rule = by_id.get(rule_id)
        if rule is None:
            errors.append(f"special policy rule missing: {rule_id}")
            continue
        if int(rule.get("item_id", -1)) != int(item_id):
            errors.append(f"{rule_id}: item_id mismatch")
        if item_id not in SPECIAL_MATERIAL_MOB_DROP_DENYLIST:
            errors.append(f"{rule_id}: item missing from mob-drop denylist")
        if rule.get("enabled"):
            errors.append(f"{rule_id}: enabled must remain False")
        if rule.get("production_enabled"):
            errors.append(f"{rule_id}: production_enabled must remain False")
        for enemy_type in ENEMY_TYPES:
            chance = (rule.get("enemy", {}).get(enemy_type, {}) or {}).get("chance")
            # The Simple Extractor retains a documented disabled 1% boss
            # candidate. It is safe only while both enable flags remain False.
            allowed_candidate = (
                item_id == 727
                and enemy_type == "boss"
                and chance == policy.get("boss_candidate_chance")
                and not rule.get("enabled")
                and not rule.get("production_enabled")
            )
            if chance not in (0, 0.0) and not allowed_candidate:
                errors.append(
                    f"{rule_id}.{enemy_type}: protected mob-drop chance {chance}"
                )
    return {"success": not errors, "errors": errors, "checked_items": sorted(SPECIAL_MATERIAL_SOURCE_POLICY)}


def validate_drop_tables(rules=None):
    """Extend canonical schema validation with protected-item policy checks."""
    base = _validate_drop_tables_schema_11_10_0(rules)
    policy = validate_special_material_drop_policy(rules)
    errors = list(base.get("errors", ())) + list(policy.get("errors", ()))
    result = dict(base)
    result["success"] = not errors
    result["errors"] = errors
    result["special_material_policy"] = policy
    return result


def assert_item_allowed_for_enemy_drop(item_id):
    """Fail closed if future generic award code targets a protected item."""
    from data.drop_tables import SPECIAL_MATERIAL_MOB_DROP_DENYLIST

    normalized = int(item_id)
    if normalized in SPECIAL_MATERIAL_MOB_DROP_DENYLIST:
        raise ValueError(
            f"item {normalized} is denied by special material mob-drop policy"
        )
    return True

# ==============================
# ROM 11.8.0 UNIVERSAL DROP SIMULATOR
# ==============================

def _simulation_mob_11_8_0(enemy_type):
    enemy_type=str(enemy_type).strip().lower()
    if enemy_type not in ENEMY_TYPES:
        raise ValueError(f"unsupported enemy_type: {enemy_type}")
    mob={"level":10,"loot_chance":0.50,"trash_items":[107,108,109]}
    if enemy_type=="elite": mob["is_elite"]=True
    elif enemy_type=="boss": mob["is_boss"]=True
    return mob


def simulate_central_drops(enemy_type,trials=10000,group="all",seed=None):
    """Simulate current central rules without DB access or item creation."""
    import random
    from collections import Counter
    enemy_type=str(enemy_type).strip().lower()
    group=str(group or "all").strip().lower()
    trials=int(trials)
    if enemy_type not in ENEMY_TYPES: raise ValueError("enemy_type must be normal, elite or boss")
    if trials<1 or trials>1000000: raise ValueError("trials must be between 1 and 1000000")
    aliases={"all":"all","rune":"rune","runes":"rune","equipment":"equipment","gear":"equipment","trophy":"trophy","loot":"trophy","material":"refine_stone","stone":"refine_stone","refine":"refine_stone","refine_stone":"refine_stone","potion":"potion","potions":"potion","special":"special"}
    if group not in aliases: raise ValueError("unsupported group")
    group=aliases[group]
    rng=random.Random(seed)
    mob=_simulation_mob_11_8_0(enemy_type)
    counts=Counter(); rarity=Counter(); rune_levels=Counter(); rune_stats=Counter(); potion_items=Counter()
    protected=Counter(); total_results=0
    selected=[]
    if group in ("all","equipment"): selected.append("equipment")
    if group in ("all","trophy"): selected.append("trophy")
    if group in ("all","refine_stone"): selected.append("refine_stone")
    if group in ("all","rune"): selected.append("rune")
    if group in ("all","potion"): selected.append("potion")
    if group in ("all","special"): selected.extend(("success_rune","simple_extractor","perfect_extractor"))
    for _ in range(trials):
        for rule_id in selected:
            rule=get_drop_rule(rule_id)
            if rule_id=="equipment": result=roll_central_equipment_drop(mob,rng.random)
            elif rule_id=="trophy": result=roll_central_trophy_simple(mob,rng.random,rng.choice)
            elif rule_id=="refine_stone": result=roll_central_refine_stone_drop(mob,rng.random)
            elif rule_id=="rune": result=roll_central_rune_drop(mob,rng.random)
            elif rule_id=="potion": result=roll_central_potion_drop(mob,rng.random)
            else: result=roll_drop_rule(rule,mob,rng.random)
            if not result.get("rolled"): continue
            total_results+=1; counts[rule_id]+=1; payload=result.get("payload") or {}
            if rule_id=="equipment": rarity[str(payload.get("rarity"))]+=1
            elif rule_id=="rune": rune_levels[int(payload.get("level",0))]+=1; rune_stats[str(payload.get("stat"))]+=1
            elif rule_id=="potion": potion_items[int(payload.get("item_id",0))]+=1
            elif rule_id in ("success_rune","simple_extractor","perfect_extractor"): protected[rule_id]+=1
    return {"enemy_type":enemy_type,"trials":trials,"group":group,"seed":seed,"counts":dict(counts),"total_results":total_results,"equipment_rarity":dict(rarity),"rune_levels":dict(rune_levels),"rune_stats":dict(rune_stats),"potion_items":dict(potion_items),"protected_items":dict(protected),"database_writes":0,"generated_equipment_rows":0}

# ==============================
# ROM 11.9.0 FINAL VICTORY DROP PLAN
# ==============================

def get_victory_drop_plan():
    """Return the single authoritative ordered production drop plan."""
    from data.drop_tables import (
        CENTRAL_DROP_VICTORY_INTEGRATION_ENABLED,
        CENTRAL_DROP_VICTORY_RULE_ORDER,
    )
    if not CENTRAL_DROP_VICTORY_INTEGRATION_ENABLED:
        raise RuntimeError("central victory integration is disabled")
    validation = validate_drop_tables()
    if not validation["success"]:
        raise RuntimeError("invalid central drop tables: " + "; ".join(validation["errors"]))
    production = {
        rule["rule_id"] for rule in DROP_RULES if rule.get("production_enabled")
    }
    plan = tuple(CENTRAL_DROP_VICTORY_RULE_ORDER)
    if set(plan) != production:
        raise RuntimeError(
            f"victory plan {plan} does not match production rules {sorted(production)}"
        )
    if len(plan) != len(set(plan)):
        raise RuntimeError("duplicate rule in central victory plan")
    return plan

