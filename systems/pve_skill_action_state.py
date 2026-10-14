# ROM 17.16.1 PVE SKILL BUTTON STATES
"""Pure, mutation-free PvE skill availability and button-state resolver."""
from __future__ import annotations

from data.mana_policy import calculate_mana_skill_cost
from data.mana_skill_presentation import format_mana_skill_presentation


def get_pve_effective_skill_cost(mob, skill):
    """Return canonical Mana cost from the battle Max MP snapshot."""
    if str(skill.get("cost_type") or "") != "mana":
        return max(0, int(skill.get("cost", 0) or 0))
    maximum = max(0, int(mob.get("player_max_mp", 0) or 0))
    return calculate_mana_skill_cost(skill, maximum)


def format_pve_skill_description(mob, skill):
    """Render clean description, effective cost and transparent formula."""
    if str(skill.get("cost_type") or "") != "mana":
        return str(skill.get("description") or "")
    maximum = max(0, int(mob.get("player_max_mp", 0) or 0))
    return format_mana_skill_presentation(skill, maximum)


def _turns_uk(value):
    value = max(0, int(value or 0))
    mod_10 = value % 10
    mod_100 = value % 100
    if mod_10 == 1 and mod_100 != 11:
        word = "хід"
    elif mod_10 in (2, 3, 4) and mod_100 not in (12, 13, 14):
        word = "ходи"
    else:
        word = "ходів"
    return f"{value} {word}"


def _state(skill, available, reason, label, message, **extra):
    key = str(skill.get("key") or "")
    result = {
        "available": bool(available),
        "reason": str(reason),
        "label": str(label),
        "message": str(message),
        "callback_data": (
            f"combat_use_skill:{key}"
            if available
            else f"skill_locked:{key}:{reason}"
        ),
    }
    result.update(extra)
    return result


def get_pve_skill_action_state(user_id, mob, skill):
    """Return current PvE skill UI state without mutating DB or combat state."""
    del user_id
    mob = mob or {}
    skill = skill or {}
    name = str(skill.get("name") or skill.get("key") or "Навичка")
    key = str(skill.get("key") or "")

    cooldowns = mob.get("skill_cooldowns") or {}
    cooldown = max(0, int(cooldowns.get(key, 0) or 0))
    if cooldown > 0:
        return _state(
            skill, False, "cooldown",
            f"⏳ {name} · ще {_turns_uk(cooldown)}",
            f"⏳ {name} ще перезаряджається. Залишилось: {_turns_uk(cooldown)}.",
            remaining=cooldown,
        )

    player_stunned = max(0, int(mob.get("player_stunned_turns", 0) or 0))
    player_effects = mob.get("player_effects") or {}
    controlled = player_stunned > 0 or any(
        str(effect.get("type") or "").lower() in {"stun", "silence", "control"}
        and int(effect.get("turns", 0) or 0) > 0
        for effect in player_effects.values()
        if isinstance(effect, dict)
    )
    if controlled:
        return _state(
            skill, False, "control_state",
            f"🔒 {name} · зараз недоступна",
            f"🔒 {name} зараз недоступна через ефект контролю.",
        )

    cost_type = str(skill.get("cost_type") or "")
    cost = get_pve_effective_skill_cost(mob, skill)

    if cost_type == "rage":
        current = max(0, int(mob.get("player_rage", 0) or 0))
        if current < cost:
            return _state(skill, False, "not_enough_rage",
                          f"🔒 {name} · потрібно {cost} Люті",
                          f"🔴 Недостатньо Люті для {name}. Потрібно: {cost}, доступно: {current}.",
                          required=cost, available_amount=current)

    elif cost_type == "rage_all_min":
        required = max(0, int(skill.get("min_cost", 30) or 30))
        current = max(0, int(mob.get("player_rage", 0) or 0))
        if current < required:
            return _state(skill, False, "not_enough_rage",
                          f"🔒 {name} · потрібно {required} Люті",
                          f"🔴 Недостатньо Люті для {name}. Потрібно мінімум: {required}, доступно: {current}.",
                          required=required, available_amount=current)

    elif cost_type in {"combat_energy", "combat_energy_combo"}:
        current = max(0, int(mob.get("player_combat_energy", 0) or 0))
        maximum = max(0, int(mob.get("player_max_combat_energy", 100) or 100))
        projected = min(maximum, current + 20)
        if projected < cost:
            return _state(skill, False, "not_enough_combat_energy",
                          f"🔒 {name} · потрібно {cost} Енергії",
                          f"🟡 Недостатньо Енергії для {name}. Потрібно: {cost}, на початку ходу буде доступно: {projected}.",
                          required=cost, available_amount=projected)
        if cost_type == "combat_energy_combo":
            required_combo = max(1, int(skill.get("min_combo", 1) or 1))
            combo = max(0, int(mob.get("player_combo_points", 0) or 0))
            if combo < required_combo:
                return _state(skill, False, "not_enough_combo",
                              f"🔒 {name} · потрібно {required_combo} комбо",
                              f"⚔️ Недостатньо комбо для {name}. Потрібно: {required_combo}, доступно: {combo}.",
                              required=required_combo, available_amount=combo)

    elif cost_type == "mana":
        current = max(0, int(mob.get("player_mp", 0) or 0))
        maximum = max(0, int(mob.get("player_max_mp", 0) or 0))
        if skill.get("key") == "mage_arcane_flow" and maximum > 0 and current >= maximum:
            return _state(skill, False, "mana_already_full",
                          f"🔒 {name} · Мана вже повна",
                          "🔵 Мана вже повна.",
                          required=cost, available_amount=current, effective_cost=cost)
        if current < cost:
            return _state(skill, False, "not_enough_mana",
                          f"🔒 {name} · потрібно {cost} Мани",
                          f"🔵 Недостатньо Мани для {name}. Потрібно: {cost}, доступно: {current}.",
                          required=cost, available_amount=current, effective_cost=cost)

    return _state(skill, True, "ok", f"✨ {name}", "", effective_cost=cost)
