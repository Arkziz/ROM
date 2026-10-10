"""Pure presentation helpers for canonical hybrid Mana skill costs."""
from __future__ import annotations
from typing import Any, Mapping
from data.mana_policy import calculate_mana_skill_cost

def strip_legacy_mana_cost_from_description(skill: Mapping[str, Any]) -> str:
    """Remove only the obsolete leading literal MP-cost sentence."""
    description = str(skill.get("description") or "").strip()
    if str(skill.get("cost_type") or "") != "mana":
        return description
    prefix = "Витрачає "
    if not description.casefold().startswith(prefix.casefold()):
        return description
    marker = description.upper().find(" MP")
    if marker < len(prefix):
        return description
    amount = description[len(prefix):marker].strip()
    if not amount.isdigit():
        return description
    tail = description[marker + 3:].lstrip()
    if tail.casefold().startswith("та "):
        tail = tail[3:].lstrip()
    elif tail.startswith((".", ",")):
        tail = tail[1:].lstrip()
    else:
        return description
    return tail[:1].upper() + tail[1:] if tail else tail


def format_mana_cost_lines(skill: Mapping[str, Any], max_mp: Any) -> str:
    """Return effective cost and transparent hybrid formula."""
    cost = calculate_mana_skill_cost(skill, max_mp)
    flat = int(skill.get("mana_cost_flat", 0) or 0)
    percent = int(skill.get("mana_cost_max_mp_percent", 0) or 0)
    cost_text = "Вартість: безкоштовно" if cost == 0 else f"Вартість: {cost} Мани"
    return f"{cost_text}\nФормула: {flat} + {percent}% максимальної мани"


def format_mana_skill_presentation(skill: Mapping[str, Any], max_mp: Any) -> str:
    """Return clean description followed by effective cost and formula."""
    description = strip_legacy_mana_cost_from_description(skill)
    lines = format_mana_cost_lines(skill, max_mp)
    return f"{description}\n{lines}" if description else lines
