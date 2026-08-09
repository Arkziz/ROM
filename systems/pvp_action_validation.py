from __future__ import annotations

from typing import Any, Mapping

from systems.pvp_config import PVP_COMBAT_ENERGY_MAX
from systems.pvp_skill_adapter import get_production_pvp_skill, load_production_pvp_skill_catalog


def projected_round_cooldown(participant: Mapping[str, Any], skill_key: str) -> int:
    """Cooldown visible to the action validator after the engine start-of-round tick."""
    stored = int(dict(participant.get("cooldowns") or {}).get(str(skill_key), 0) or 0)
    return max(0, stored - 1)


def projected_round_resource(participant: Mapping[str, Any]) -> int:
    value = int(participant.get("resource_value", participant.get("resource", 0)) or 0)
    if str(participant.get("resource_type") or "") in {"combat_energy", "combat_energy_combo"}:
        return min(PVP_COMBAT_ENERGY_MAX, value + 20)
    return value


def validate_pvp_action_choice(
    participant: Mapping[str, Any],
    action_type: str,
    skill_key: str | None = None,
    *,
    catalog: Mapping[str, tuple[dict[str, Any], ...]] | None = None,
) -> dict[str, Any]:
    """Prevalidate a UI action without mutating state or consuming the round.

    The pure round engine remains the final authority. This helper mirrors the
    engine's imminent start-of-round cooldown tick and Combat Energy regeneration
    so a choice accepted by the UI is not rejected later for stale resource data.
    """
    action_type = str(action_type or "")
    if action_type == "basic_attack":
        return {"success": True, "reason": "ok", "message": ""}
    if action_type != "skill" or not skill_key:
        return {"success": False, "reason": "invalid_action", "message": "❌ Невідома бойова дія. Оберіть іншу дію."}

    class_key = str(participant.get("class_key") or "")
    skill = get_production_pvp_skill(class_key, str(skill_key), catalog or load_production_pvp_skill_catalog())
    if not skill:
        return {"success": False, "reason": "unknown_skill", "message": "❌ Ця навичка не належить вашому класу. Оберіть іншу дію."}

    name = str(skill.get("name") or skill_key)
    cooldown = projected_round_cooldown(participant, str(skill_key))
    if cooldown > 0:
        return {
            "success": False,
            "reason": "skill_on_cooldown",
            "remaining": cooldown,
            "message": f"⏳ «{name}» ще відновлюється. Залишилося раундів: {cooldown}. Оберіть іншу дію.",
        }

    cost_type = str(skill.get("cost_type") or "")
    cost = max(0, int(skill.get("cost") or 0))
    resource = projected_round_resource(participant)
    mp = int(participant.get("mp") or 0)
    combo = int(participant.get("combo") or 0)

    if cost_type == "mana" and mp < cost:
        return {"success": False, "reason": "not_enough_mana", "required": cost, "available": mp, "message": f"🔷 Недостатньо мани для «{name}». Потрібно: {cost} MP, доступно: {mp} MP. Оберіть іншу дію."}
    if cost_type == "rage" and resource < cost:
        return {"success": False, "reason": "not_enough_rage", "required": cost, "available": resource, "message": f"🔥 Недостатньо Люті для «{name}». Потрібно: {cost}, доступно: {resource}. Оберіть іншу дію."}
    if cost_type == "rage_all_min":
        minimum = max(0, int(skill.get("min_cost") or 0))
        if resource < minimum:
            return {"success": False, "reason": "not_enough_rage", "required": minimum, "available": resource, "message": f"🔥 Недостатньо Люті для «{name}». Потрібно щонайменше: {minimum}, доступно: {resource}. Оберіть іншу дію."}
    if cost_type in {"combat_energy", "combat_energy_combo"} and resource < cost:
        return {"success": False, "reason": "not_enough_combat_energy", "required": cost, "available": resource, "message": f"⚡ Недостатньо Енергії для «{name}». Потрібно: {cost}, після відновлення доступно: {resource}. Оберіть іншу дію."}
    if cost_type == "combat_energy_combo":
        minimum_combo = int(skill.get("min_combo") or 1)
        if combo < minimum_combo:
            return {"success": False, "reason": "not_enough_combo", "required": minimum_combo, "available": combo, "message": f"🔗 Недостатньо комбо для «{name}». Потрібно: {minimum_combo}, доступно: {combo}. Оберіть іншу дію."}

    return {
        "success": True,
        "reason": "ok",
        "message": "",
        "skill": dict(skill),
        "projected_resource": resource,
        "projected_cooldown": cooldown,
    }


def pvp_skill_button_state(participant: Mapping[str, Any], skill: Mapping[str, Any]) -> dict[str, Any]:
    result = validate_pvp_action_choice(participant, "skill", str(skill.get("key") or ""), catalog={str(participant.get("class_key") or ""): (dict(skill),)})
    name = str(skill.get("name") or skill.get("key") or "Навичка")
    if result.get("success"):
        return {"available": True, "label": f"✨ {name}", "reason": "ok"}
    if result.get("reason") == "skill_on_cooldown":
        return {"available": False, "label": f"⏳ {name} · {int(result.get('remaining') or 0)}", "reason": result.get("reason")}
    return {"available": False, "label": f"🔒 {name}", "reason": result.get("reason")}
