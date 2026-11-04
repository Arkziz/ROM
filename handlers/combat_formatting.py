# -*- coding: utf-8 -*-
"""Pure combat text formatting owners extracted from handlers.combat."""
from __future__ import annotations

def build_lethal_combat_log(turn_context, player_hp, player_max_hp, durability_damage):
    """Preserve the terminal turn narrative and live enemy HP before death cleanup."""
    # ROM 17.3.0 PVE DEFEAT ENEMY HP
    context = dict(turn_context or {})
    parts = []

    for key in (
        "cooldown_start_text",
        "player_effects_text",
        "resource_start_text",
        "resource_attack_text",
        "cooldown_set_text",
        "special_effect_text",
        "enemy_effect_text",
    ):
        value = context.get(key)
        if value:
            parts.append(str(value).strip())

    skill = context.get("skill")
    skill_hit = context.get("skill_hit")
    if isinstance(skill, dict) and skill.get("name"):
        if skill_hit is False:
            parts.append("💨 ПРОМАХ! Навичка «{}» не влучила в ціль.".format(skill["name"]))
        elif skill.get("no_damage"):
            parts.append(f"✨ {skill['name']}\n✨ Навичка застосована.")
        elif context.get("dmg") is not None:
            parts.append(f"✨ {skill['name']}\n✨ Ти завдав {max(0, int(context.get('dmg') or 0))} шкоди.")
    elif context.get("dmg") is not None:
        parts.append(f"⚔️ Ти завдав {max(0, int(context.get('dmg') or 0))} шкоди.")

    enemy_action_text = context.get("enemy_action_text")
    if enemy_action_text:
        parts.append(str(enemy_action_text).strip())

    unique_parts = []
    for part in parts:
        if part and part not in unique_parts:
            unique_parts.append(part)

    from handlers.combat import build_death_text
    death_text = build_death_text(durability_damage)
    death_heading, _, death_tail = death_text.partition("\n")
    text = f"{death_heading}\n\n💥 ОСТАННІЙ ХІД\n\n"
    if unique_parts:
        text += "\n".join(unique_parts) + "\n\n"

    # ROM 17.3.0.2 REMOVE REDUNDANT PLAYER HP BEFORE DEFEAT
    mob = context.get("mob")
    if isinstance(mob, dict):
        enemy_name = str(mob.get("name") or "Противник")
        try:
            enemy_current_hp = max(0, int(round(float(mob.get("hp", 0) or 0))))
        except Exception:
            enemy_current_hp = 0
        try:
            enemy_max_hp = max(1, int(round(float(mob.get("max_hp", enemy_current_hp) or enemy_current_hp or 1))))
        except Exception:
            enemy_max_hp = max(1, enemy_current_hp)
        enemy_current_hp = min(enemy_current_hp, enemy_max_hp)
        text += f"👹 Противник: {enemy_name}\n"
        text += f"❤️ Здоров’я противника: {enemy_current_hp}/{enemy_max_hp}\n\n"

    if death_tail:
        text += death_tail.lstrip("\n")
    return text
