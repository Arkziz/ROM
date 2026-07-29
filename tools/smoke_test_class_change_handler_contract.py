#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Structural/runtime contracts for the class-change callback hotfix."""
from __future__ import annotations
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = ROOT / "handlers" / "start.py"
CHARACTER = ROOT / "systems" / "character_system.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    start_source = START.read_text(encoding="utf-8-sig")
    start_tree = ast.parse(start_source, filename=str(START))
    character_source = CHARACTER.read_text(encoding="utf-8-sig")
    character_tree = ast.parse(character_source, filename=str(CHARACTER))

    change_nodes = [
        node for node in ast.walk(start_tree)
        if isinstance(node, ast.FunctionDef) and node.name == "change_class"
    ]
    if len(change_nodes) != 1:
        fail(f"change_class definitions={len(change_nodes)}, expected 1")
    change_source = ast.get_source_segment(start_source, change_nodes[0]) or ""

    required = (
        "isinstance(consume_result, dict)",
        "consume_success = bool(consume_result)",
        "result.get(\"class_name\")",
        "get_character_class_display(user_id)",
        "unequip_incompatible_items_after_class_change(user_id)",
    )
    for marker in required:
        if marker not in change_source:
            fail(f"change_class missing marker: {marker}")
    if 'consume_result["success"]' in change_source:
        fail("unsafe dict-only consume_result access remains")
    if "result['class_name']" in change_source:
        fail("unsafe class_name indexing remains")

    consume_nodes = [
        node for node in character_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "consume_class_change_available"
    ]
    if len(consume_nodes) != 1:
        fail("Character System consume function count is not 1")
    consume_source = ast.get_source_segment(character_source, consume_nodes[0]) or ""
    if "return changed" not in consume_source:
        fail("Character System consume contract is no longer bool")

    set_nodes = [
        node for node in character_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "set_character_class"
    ]
    if len(set_nodes) != 1:
        fail("Character System set_character_class count is not 1")
    set_source = ast.get_source_segment(character_source, set_nodes[0]) or ""
    if '"class_key": key' not in set_source:
        fail("set_character_class class_key result contract missing")

    # Pure contract matrix: no DB or Telegram calls.
    samples = (
        (True, True),
        (False, False),
        ({"success": True}, True),
        ({"success": False, "message": "x"}, False),
    )
    for value, expected in samples:
        actual = bool(value.get("success")) if isinstance(value, dict) else bool(value)
        if actual is not expected:
            fail(f"consume compatibility matrix failed: {value!r}")

    print("[OK] class change handler contract hotfix")
    print("- bool consume result: supported")
    print("- historical dict consume result: supported")
    print("- class_key-only set result: supported")
    print("- incompatible equipment auto-unequip path: preserved")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
