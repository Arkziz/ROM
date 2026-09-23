#!/usr/bin/env python3
"""Maintained source check for the Daily Quest Town Hall return contract."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse(relative):
    source = (ROOT / relative).read_text(encoding="utf-8-sig")
    return source, ast.parse(source, filename=relative)


def functions(tree, name):
    return sorted(
        [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name],
        key=lambda node: node.lineno,
    )


def main():
    keyboard_source, keyboard_tree = parse("keyboards.py")
    daily_source, daily_tree = parse("handlers/daily.py")

    keyboard_defs = functions(keyboard_tree, "daily_quest_kb")
    assert len(keyboard_defs) == 1
    keyboard_text = ast.get_source_segment(keyboard_source, keyboard_defs[0])
    assert keyboard_text.count("🔙 Ратуша") == 1
    assert "🗣️ Староста" not in keyboard_text
    assert "📆 Щоденне завдання" not in keyboard_text
    assert "🔙 Місто" not in keyboard_text

    register_defs = functions(daily_tree, "register_daily_handlers")
    assert register_defs
    register_text = ast.get_source_segment(daily_source, register_defs[-1])
    assert "daily_quest_kb" in daily_source
    assert register_text.count("reply_markup=daily_quest_kb()") >= 2
    # The informational location message remains valid. The regression concerns
    # only its reply keyboard, which must now be the focused Town Hall return.
    assert "Ви знаходитесь у Ратуші" in register_text
    assert "reply_markup=townhall_kb()" not in register_text
    print("[PASS] Daily Quest Town Hall return keyboard")


if __name__ == "__main__":
    main()
