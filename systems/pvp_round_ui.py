from __future__ import annotations

from html import escape
from typing import Any, Mapping
from telebot import types

from systems.pvp_skill_adapter import load_production_pvp_skill_catalog


def _bar(current: int, maximum: int, width: int = 10) -> str:
    maximum=max(1,int(maximum)); current=max(0,min(int(current),maximum))
    filled=int(round(width*current/maximum))
    return "█"*filled+"░"*(width-filled)


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
        f"<b>Ви</b>\n❤️ {_bar(own_hp,own_max)} {own_hp}/{own_max}\n{_resource_line(viewer)}\n\n"
        f"<b>Суперник</b>\n❤️ {_bar(foe_hp,foe_max)} {foe_hp}/{foe_max}"
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
        key=str(skill.get("key") or ""); name=str(skill.get("name") or key)
        cd=int(cooldowns.get(key,0) or 0)
        label=f"✨ {name}"+(f" · ⏳ {cd}" if cd>0 else "")
        kb.add(types.InlineKeyboardButton(label,callback_data=f"pvp:round:act:{bid}:{rnd}:{rev}:skill:{key}"))
    kb.add(types.InlineKeyboardButton("🔄 Оновити стан",callback_data=f"pvp:round:refresh:{bid}:{rnd}:{rev}"))
    return kb
