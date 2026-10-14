#!/usr/bin/env python3
"""Maintained source-shaped check for the three new production NPC routes."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_npcs import STORY_QUEST_NPCS, get_missing_story_quest_npc_routes


def parse(relative):
    source = (ROOT / relative).read_text(encoding="utf-8-sig")
    return source, ast.parse(source, filename=relative)


def functions(tree, name):
    return [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]


def main():
    keyboard_source, keyboard_tree = parse("keyboards.py")
    city_source, city_tree = parse("handlers/city.py")

    contracts = {
        "elder": ("townhall_kb", "elder_kb", "🗣️ Староста", "🔙 Ратуша"),
        "mercenary_head": (
            "guild_kb", "mercenary_head_kb", "⚔️ Голова Найманців",
            "🔙 Гільдія Найманців",
        ),
        "bartender": ("tavern_kb", "bartender_kb", "🍺 Бармен", "🔙 Таверна"),
    }
    for npc_id, (section_fn, npc_fn, label, back_label) in contracts.items():
        assert STORY_QUEST_NPCS[npc_id].production_route_exists
        section_defs = functions(keyboard_tree, section_fn)
        npc_defs = functions(keyboard_tree, npc_fn)
        assert len(section_defs) == 1 and len(npc_defs) == 1
        assert label in ast.get_source_segment(keyboard_source, section_defs[0])
        assert back_label in ast.get_source_segment(keyboard_source, npc_defs[0])

    assert get_missing_story_quest_npc_routes() == ()
    register_defs = sorted(
        functions(city_tree, "register_city_handlers"), key=lambda node: node.lineno
    )
    assert register_defs
    register_text = ast.get_source_segment(city_source, register_defs[-1])
    for label in (
        "🗣️ Староста", "⚔️ Голова Найманців", "🍺 Бармен",
        "🔙 Ратуша", "🔙 Гільдія Найманців", "🔙 Таверна",
    ):
        assert register_text.count(label) == 1
    for helper in (
        "build_story_elder_text", "build_story_mercenary_head_text",
        "build_story_bartender_text",
    ):
        assert len(functions(city_tree, helper)) == 1
    assert "accept_story_quest" not in register_text
    assert "complete_active_story_quest" not in register_text
    print("[PASS] missing story quest NPC production routes")


if __name__ == "__main__":
    main()
