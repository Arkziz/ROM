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


def render_pvp_round_combat_log(payload: Mapping[str, Any], viewer_user_id: int) -> str:
    """Render one resolved round from the viewer's perspective.

    This function is presentation-only. It does not mutate PvP or production state.
    """
    viewer = int(viewer_user_id)
    round_number = int(payload.get("round_number") or 0)
    actors = {int(x.get("user_id")): x for x in payload.get("actors", ()) if isinstance(x, Mapping) and x.get("user_id") is not None}
    lines = [f"⚔️ <b>Результат раунду {round_number}</b>"]

    for outcome in payload.get("outcomes", ()):
        if not isinstance(outcome, Mapping):
            continue
        uid = int(outcome.get("user_id") or 0)
        actor = actors.get(uid, {})
        who = _actor_display_name(actor, uid)
        action_type = str(outcome.get("action_type") or "")
        if action_type == "afk_skip":
            lines.append(f"\n⏳ <b>{escape(who)}</b>: пропуск через бездіяльність.")
            continue
        if action_type == "stunned_skip":
            lines.append(f"\n⚡ <b>{escape(who)}</b>: пропуск через оглушення.")
            continue
        if not bool(outcome.get("valid")):
            lines.append(f"\n⚠️ <b>{escape(who)}</b>: дія не виконана ({escape(str(outcome.get('reason') or 'невідома причина'))}).")
            continue
        name = escape(_skill_name(str(actor.get("class_key") or ""), outcome.get("skill_key")))
        lines.append(f"\n<b>{escape(who)}</b> використав: {name}.")
        if bool(outcome.get("dodged")):
            lines.append("💨 Атаку було ухилено.")
        elif int(outcome.get("damage") or 0) > 0:
            crit = " 💥 Критичний удар." if bool(outcome.get("critical")) else ""
            lines.append(f"🗡 Завдано <b>{int(outcome.get('damage') or 0)}</b> шкоди.{crit}")
        if int(outcome.get("healing") or 0) > 0:
            lines.append(f"❤️ Відновлено <b>{int(outcome.get('healing') or 0)}</b> HP.")
        if int(outcome.get("resource_spent") or 0) > 0:
            lines.append(f"🔹 Витрачено ресурсу: {int(outcome.get('resource_spent') or 0)}.")
        if int(outcome.get("resource_gained") or 0) > 0:
            lines.append(f"🔹 Отримано ресурсу: {int(outcome.get('resource_gained') or 0)}.")
        if int(outcome.get("combo_spent") or 0) > 0:
            lines.append(f"🔗 Витрачено комбо: <b>{int(outcome.get('combo_spent') or 0)}</b>. Після навички: 0/3.")
        if int(outcome.get("combo_gained") or 0) > 0:
            combo_after = int(actor.get("combo") or 0)
            lines.append(f"🔗 Отримано комбо: {int(outcome.get('combo_gained') or 0)}. Тепер: {combo_after}/3.")
        for effect in outcome.get("applied_effects", ()):
            if not isinstance(effect, Mapping):
                continue
            key = str(effect.get("effect_key") or effect.get("kind") or "effect")
            label = escape(_effect_label(key))
            duration = int(effect.get("duration") or 0)
            power = int(round(float(effect.get("power") or 0)))
            suffix = f" на {duration} раунд(и)" if duration > 0 else ""
            if key == "hot":
                lines.append(f"🌿 Накладено відновлення здоров'я{suffix}: до {power} HP на початку кожного наступного раунду.")
            elif key == "shield":
                lines.append(f"🛡️ Накладено щит{suffix}: {power} поглинання.")
            elif key == "mana_restore":
                lines.append(f"🔷 Відновлено мани: {power}.")
            elif key == "stun_next":
                lines.append("⚡ Накладено оглушення на наступний раунд.")
            else:
                lines.append(f"✨ Накладено ефект: {label}{suffix}.")

    for event in payload.get("events", ()):
        if not isinstance(event, Mapping):
            continue
        kind = str(event.get("type") or "")
        uid = int(event.get("user_id") or 0)
        who = _actor_display_name(actors.get(uid, {}), uid)
        value = int(event.get("value") or 0)
        effect = escape(_effect_label(str(event.get("effect") or "effect")))
        if kind == "dot_tick":
            lines.append(f"\n{effect}: <b>{escape(who)}</b> отримує <b>{value}</b> шкоди.")
        elif kind == "hot_tick":
            current_hp = event.get("hp_after")
            max_hp = event.get("max_hp")
            extra = f" HP стало {int(current_hp)}/{int(max_hp)}." if current_hp is not None and max_hp is not None else ""
            lines.append(f"\n🌿 <b>{escape(who)}</b>: фактично відновлено <b>{value}</b> HP.{extra}")
        elif kind == "shield_absorb":
            lines.append(f"\n🛡️ <b>{escape(who)}</b>: щит поглинув <b>{value}</b> шкоди.")
        elif kind == "effect_expired":
            lines.append(f"\n⌛ <b>{escape(who)}</b>: ефект {effect} завершився.")
        elif kind == "combat_energy_regen":
            before = int(event.get("before") or 0)
            after = int(event.get("after") or 0)
            maximum = int(event.get("maximum") or 100)
            lines.append(f"\n⚡ <b>{escape(who)}</b>: Енергія {before} → {after}/{maximum}.")
        elif kind == "rage_gain_attack":
            before = int(event.get("before") or 0)
            after = int(event.get("after") or 0)
            lines.append(f"\n🔥 <b>{escape(who)}</b>: +{value} Люті за атаку ({before} → {after}/100).")
        elif kind == "rage_gain_skill":
            before = int(event.get("before") or 0)
            after = int(event.get("after") or 0)
            lines.append(f"\n🔥 <b>{escape(who)}</b>: +{value} додаткової Люті від навички ({before} → {after}/100).")
        elif kind == "rage_gain_damage_taken":
            before = int(event.get("before") or 0)
            after = int(event.get("after") or 0)
            lines.append(f"\n🔥 <b>{escape(who)}</b>: +{value} Люті за отриману шкоду ({before} → {after}/100).")

    return "\n".join(lines)
