from __future__ import annotations

from html import escape
from typing import Any, Mapping
from telebot import types

from systems.pvp_skill_adapter import load_production_pvp_skill_catalog
from systems.pvp_action_validation import pvp_skill_button_state


def _bar(current: int, maximum: int, width: int = 10) -> str:
    maximum=max(1,int(maximum)); current=max(0,min(int(current),maximum))
    filled=int(round(width*current/maximum))
    return "█"*filled+"░"*(width-filled)


def _participant_display_name(participant: Mapping[str, Any]) -> str:
    snapshot = participant.get("snapshot") if isinstance(participant.get("snapshot"), Mapping) else {}
    name = str(participant.get("character_name") or snapshot.get("character_name") or "").strip()
    if not name:
        try:
            from db import get_character_name
            name = str(get_character_name(int(participant.get("user_id") or 0)) or "").strip()
        except Exception:
            name = ""
    return name or f"Гравець #{int(participant.get('user_id') or 0)}"


def _resource_line(participant: Mapping[str, Any]) -> str:
    kind=str(participant.get("resource_type") or "")
    value=int(participant.get("resource_value") or 0)
    if kind=="mana": return f"🔷 MP: {int(participant.get('mp') or 0)}/{int(participant.get('max_mp') or 0)}"
    if kind=="rage": return f"🔥 Лють: {value}/100"
    if kind=="combat_energy_combo": return f"⚡ Енергія: {value}/100  🔗 Комбо: {int(participant.get('combo') or 0)}/3"
    if kind=="combat_energy": return f"⚡ Енергія: {value}/100"
    return f"🔹 Ресурс: {value}/100"


def render_pvp_round_text(battle: Mapping[str, Any], viewer: Mapping[str, Any], enemy: Mapping[str, Any], waiting: bool=False) -> str:
    # Deliberately no '/50': players see only the current round number.
    round_number=int(battle.get("round_number") or 1)
    own_hp=int(viewer.get("hp") or 0); own_max=int(viewer.get("max_hp") or 1)
    foe_hp=int(enemy.get("hp") or 0); foe_max=int(enemy.get("max_hp") or 1)
    status="\n\n⏳ Вашу дію прийнято. Очікуємо суперника." if waiting else "\n\nОберіть дію. На вибір є 20 секунд."
    return (
        f"⚔️ <b>PvP-дуель</b>\n\n"
        f"<b>Раунд {round_number}</b>\n\n"
        f"<b>{escape(_participant_display_name(viewer))}</b>\n❤️ {_bar(own_hp,own_max)} {own_hp}/{own_max}\n{_resource_line(viewer)}\n\n"
        f"<b>{escape(_participant_display_name(enemy))}</b>\n❤️ {_bar(foe_hp,foe_max)} {foe_hp}/{foe_max}"
        f"{status}"
    )


def build_pvp_action_keyboard(battle: Mapping[str, Any], participant: Mapping[str, Any], *, action_submitted: bool=False):
    kb=types.InlineKeyboardMarkup(row_width=1)
    bid=int(battle["id"]); rnd=int(battle["round_number"]); rev=int(battle["revision"])
    if action_submitted:
        kb.add(types.InlineKeyboardButton("🔄 Оновити стан",callback_data=f"pvp:round:refresh:{bid}:{rnd}:{rev}"))
        return kb
    kb.add(types.InlineKeyboardButton("⚔️ Звичайна атака",callback_data=f"pvp:round:act:{bid}:{rnd}:{rev}:basic_attack"))
    catalog=load_production_pvp_skill_catalog()
    skills=catalog.get(str(participant.get("class_key") or ""),())
    cooldowns=dict(participant.get("cooldowns") or {})
    for skill in skills:
        key=str(skill.get("key") or "")
        state=pvp_skill_button_state(participant,skill)
        kb.add(types.InlineKeyboardButton(str(state.get("label") or skill.get("name") or key),callback_data=f"pvp:round:act:{bid}:{rnd}:{rev}:skill:{key}"))
    kb.add(types.InlineKeyboardButton("🔄 Оновити стан",callback_data=f"pvp:round:refresh:{bid}:{rnd}:{rev}"))
    return kb
