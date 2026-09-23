#!/usr/bin/env python3
"""Maintained source-shaped check for the Profile story-quest route."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse(relative):
    source = (ROOT / relative).read_text(encoding="utf-8-sig")
    return source, ast.parse(source, filename=relative)


def functions(tree, name):
    return [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]


def main():
    keyboard_source, keyboard_tree = parse("keyboards.py")
    profile_source, profile_tree = parse("handlers/profile.py")
    story_source, story_tree = parse("handlers/story_quests.py")
    main_source, main_tree = parse("main.py")

    profile_keyboards = functions(keyboard_tree, "profile_kb")
    assert len(profile_keyboards) == 1
    profile_keyboard_text = ast.get_source_segment(keyboard_source, profile_keyboards[0])
    assert profile_keyboard_text.count("📜 Квести") == 1
    assert "🎒 Інвентар" in profile_keyboard_text
    assert "📜 Історія" in profile_keyboard_text
    assert "🔙 Назад" in profile_keyboard_text

    send_roots = functions(profile_tree, "send_profile_root")
    assert len(send_roots) == 1
    assert "build_character_text" in ast.get_source_segment(profile_source, send_roots[0])
    profile_handlers = functions(profile_tree, "profile")
    assert len(profile_handlers) == 1
    assert "send_profile_root" in ast.get_source_segment(profile_source, profile_handlers[0])

    registers = functions(story_tree, "register_story_quest_handlers")
    assert len(registers) == 1
    registration_text = ast.get_source_segment(story_source, registers[0])
    assert "STORY_QUEST_BUTTON_TEXT" in registration_text
    assert "story_quest:" in story_source
    assert "accept_story_quest" not in registration_text
    assert "complete_active_story_quest" not in registration_text
    assert "send_profile_root" in registration_text
    assert "_edit_story_journal_safely" in registration_text
    assert "message is not modified" in story_source

    assert "from handlers.story_quests import register_story_quest_handlers" in main_source
    profile_position = main_source.index("register_profile_handlers(bot)")
    story_position = main_source.index("register_story_quest_handlers(bot)")
    inventory_position = main_source.index("register_inventory_handlers(bot)")
    assert profile_position < story_position < inventory_position
    print("[PASS] story quest Profile production route")


if __name__ == "__main__":
    main()
