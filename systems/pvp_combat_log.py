from __future__ import annotations

from html import escape
from typing import Any, Mapping, Sequence

from systems.pvp_skill_adapter import load_production_pvp_skill_catalog

_EFFECT_LABELS = {
    "poison": "☠️ Отруєння",
    "bleed": "🩸 Кровотеча",
    "dot": "🔥 Періодична шкода",
    "hot": "🌿 Відновлення здоров'я",
    "heal_over_time": "🌿 Відновлення здоров'я",
    "pdef_down": "🛡️ Зниження фізичного захисту",
    "mdef_down": "🔮 Зниження магічного захисту",
    "mdef_buff": "🔮 Підвищення магічного захисту",
    "shield": "🛡️ Щит",
    "stun_next": "⚡ Оглушення",
    "mana_restore": "🔷 Відновлення мани",
}


def _skill_name(class_key: str, skill_key: str | None) -> str:
    if not skill_key:
        return "Звичайна атака"
    for skill in load_production_pvp_skill_catalog().get(str(class_key or ""), ()):
        if str(skill.get("key") or "") == str(skill_key):
            return str(skill.get("name") or skill_key)
    return str(skill_key)


def _effect_label(key: str) -> str:
    return _EFFECT_LABELS.get(str(key or ""), str(key or "ефект"))


def _actor_display_name(actor: Mapping[str, Any], user_id: int) -> str:
    name = str(actor.get("character_name") or "").strip()
    if not name:
        try:
            from db import get_character_name
            name = str(get_character_name(int(user_id)) or "").strip()
        except Exception:
            name = ""
    return name or f"Гравець #{int(user_id)}"


def _round_word(value: int) -> str:
    value = abs(int(value))
    if value % 10 == 1 and value % 100 != 11:
        return "раунд"
    if value % 10 in {2, 3, 4} and value % 100 not in {12, 13, 14}:
        return "раунди"
    return "раундів"


def _resource_meta(actor: Mapping[str, Any]) -> tuple[str, str]:
    resource_type = str(actor.get("resource_type") or "")
    if resource_type == "rage":
        return "🔥", "Лють"
    if resource_type in {"combat_energy", "combat_energy_combo"}:
        return "⚡", "Енергія"
    return "🔷", "Мана"


def _resource_value(actor: Mapping[str, Any]) -> tuple[int, int]:
    resource_type = str(actor.get("resource_type") or "")
    if resource_type == "mana":
        return int(actor.get("mp") or 0), int(actor.get("max_mp") or 0)
    return int(actor.get("resource") or 0), 100


def _state_lines(actors: Mapping[int, Mapping[str, Any]]) -> list[str]:
    ordered = list(actors.items())
    hp = " | ".join(
        f"{escape(_actor_display_name(actor, uid))}: {int(actor.get('hp') or 0)}/{int(actor.get('max_hp') or 0)}"
        for uid, actor in ordered
    )
    resources = []
    for uid, actor in ordered:
        icon, label = _resource_meta(actor)
        current, maximum = _resource_value(actor)
        resources.append(f"{icon} {escape(_actor_display_name(actor, uid))}: {current}/{maximum} {label}")
    return [f"❤️ {hp}", " | ".join(resources)]


def render_pvp_round_combat_log(payload: Mapping[str, Any], viewer_user_id: int) -> str:
    """Render a compact PvP round log with resource events grouped by owner."""
    round_number = int(payload.get("round_number") or 0)
    actors = {
        int(item.get("user_id")): item
        for item in payload.get("actors", ())
        if isinstance(item, Mapping) and item.get("user_id") is not None
    }
    events = [item for item in payload.get("events", ()) if isinstance(item, Mapping)]
    lines = [f"⚔️ <b>Раунд {round_number}</b>"]

    action_rage: dict[int, list[Mapping[str, Any]]] = {}
    damage_rage: list[Mapping[str, Any]] = []
    for event in events:
        kind = str(event.get("type") or "")
        uid = int(event.get("user_id") or 0)
        if kind in {"rage_gain_attack", "rage_gain_skill"}:
            action_rage.setdefault(uid, []).append(event)
        elif kind == "rage_gain_damage_taken":
            damage_rage.append(event)

    # Start-of-round events are displayed before combat actions.
    for event in events:
        kind = str(event.get("type") or "")
        if kind not in {"dot_tick", "hot_tick", "combat_energy_regen", "effect_expired"}:
            continue
        uid = int(event.get("user_id") or 0)
        who = escape(_actor_display_name(actors.get(uid, {}), uid))
        value = int(event.get("value") or 0)
        effect_label = escape(_effect_label(str(event.get("effect") or "effect")))
        effect_text = effect_label.replace("🛡️ ", "").replace("🩸 ", "").replace("☠️ ", "")
        if kind == "dot_tick":
            lines.append(f"{effect_label}: <b>{who}</b> отримує <b>{value}</b> шкоди.")
        elif kind == "hot_tick":
            lines.append(f"🌿 <b>{who}</b>: відновлено <b>{value}</b> HP.")
        elif kind == "combat_energy_regen":
            before = int(event.get("before") or 0)
            after = int(event.get("after") or 0)
            maximum = int(event.get("maximum") or 100)
            lines.append(f"⚡ <b>{who}</b>: +{value} Енергії → {after}/{maximum}")
        elif kind == "effect_expired":
            lines.append(f"⌛ <b>{who}</b>: {effect_text.lower()} завершилося")

    for outcome in payload.get("outcomes", ()):
        if not isinstance(outcome, Mapping):
            continue
        uid = int(outcome.get("user_id") or 0)
        actor = actors.get(uid, {})
        who = escape(_actor_display_name(actor, uid))
        action_type = str(outcome.get("action_type") or "")
        lines.append("")

        if action_type == "afk_skip":
            lines.append(f"⏳ <b>{who}</b> пропускає хід через бездіяльність")
            continue
        if action_type == "stunned_skip":
            lines.append(f"⚡ <b>{who}</b> оглушений і пропускає хід")
            continue
        if not bool(outcome.get("valid")):
            lines.append(f"⚠️ <b>{who}</b>: дію не виконано")
            continue

        skill_name = escape(_skill_name(str(actor.get("class_key") or ""), outcome.get("skill_key")))
        lines.append(f"<b>{who}</b> використав: {skill_name}.")
        if bool(outcome.get("dodged")):
            lines.append("💨 Суперник ухилився від атаки")
        elif int(outcome.get("damage") or 0) > 0:
            critical = " 💥 Критичний удар." if bool(outcome.get("critical")) else ""
            lines.append(f"🗡 Завдано <b>{int(outcome.get('damage') or 0)}</b> шкоди.{critical}")
        if int(outcome.get("healing") or 0) > 0:
            lines.append(f"❤️ Відновлено <b>{int(outcome.get('healing') or 0)}</b> HP.")

        icon, label = _resource_meta(actor)
        spent = int(outcome.get("resource_spent") or 0)
        gained = int(outcome.get("resource_gained") or 0)
        if spent > 0:
            lines.append(f"{icon} {label}: −{spent}")

        owner_rage = action_rage.get(uid, ())
        if owner_rage:
            total = sum(int(event.get("value") or 0) for event in owner_rage)
            after = int(owner_rage[-1].get("after") or actor.get("resource") or 0)
            lines.append(f"🔥 Лють: +{total} → {after}/100")
        elif gained > 0:
            lines.append(f"{icon} {label}: +{gained}")

        if int(outcome.get("combo_spent") or 0) > 0:
            lines.append(f"🔗 Комбо: −{int(outcome.get('combo_spent') or 0)} → 0/3")
        if int(outcome.get("combo_gained") or 0) > 0:
            lines.append(f"🔗 Комбо: +{int(outcome.get('combo_gained') or 0)} → {int(actor.get('combo') or 0)}/3")

        for effect in outcome.get("applied_effects", ()):
            if not isinstance(effect, Mapping):
                continue
            key = str(effect.get("effect_key") or effect.get("kind") or "effect")
            duration = int(effect.get("duration") or 0)
            power = int(round(float(effect.get("power") or 0)))
            suffix = f", {duration} {_round_word(duration)}" if duration > 0 else ""
            if key == "hot":
                lines.append(f"🌿 Відновлення здоров’я{suffix}")
            elif key == "shield":
                lines.append(f"🛡️ Накладено щит на {duration} {_round_word(duration)}." if duration else "🛡️ Накладено щит.")
            elif key == "mana_restore":
                lines.append(f"🔷 Мана: +{power}")
            elif key == "stun_next":
                lines.append("⚡ Оглушення на наступний раунд")
            elif key == "bleed":
                lines.append(f"🩸 Кровотеча{suffix}")
            elif key == "poison":
                lines.append(f"☠️ Отруєння{suffix}")
            else:
                lines.append(f"{escape(_effect_label(key))}{suffix}")

    # Incoming-damage Rage belongs to the damaged character, so the owner name is mandatory.
    for event in damage_rage:
        uid = int(event.get("user_id") or 0)
        who = escape(_actor_display_name(actors.get(uid, {}), uid))
        value = int(event.get("value") or 0)
        after = int(event.get("after") or actors.get(uid, {}).get("resource") or 0)
        lines.append(f"🔥 <b>{who}</b>: +{value} Люті від отриманої шкоди → {after}/100")

    for event in events:
        if str(event.get("type") or "") != "shield_absorb":
            continue
        uid = int(event.get("user_id") or 0)
        who = escape(_actor_display_name(actors.get(uid, {}), uid))
        value = int(event.get("value") or 0)
        lines.append(f"🛡️ <b>{who}</b>: щит поглинув <b>{value}</b> шкоди.")

    lines.append("")
    lines.extend(_state_lines(actors))
    return "\n".join(lines)

