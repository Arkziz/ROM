#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDLER = ROOT / "handlers" / "player_interaction.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    source = HANDLER.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(HANDLER))
    if "ROM 12.7.0C PLAYER TRADE FIRST READY STATUS AND COMPLETION TEXT FIX" not in source:
        fail("12.7.0c marker missing")

    editors = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_trade_editor_text"
    ]
    if len(editors) != 1:
        fail(f"editor function count: {len(editors)}")
    editor_source = ast.get_source_segment(source, editors[0]) or ""
    if editor_source.count("_trade_ready_status_text_12_7_0(state)") != 1:
        fail("ready status is not rendered exactly once in trade editor")
    status_position = editor_source.find("_trade_ready_status_text_12_7_0(state)")
    note_position = editor_source.find("Редагування пропозиції скидає готовність")
    if status_position < 0 or note_position < 0 or status_position > note_position:
        fail("ready status is not placed above editor reset note")

    if "Предмети та золото передано атомарно." in source:
        fail("technical atomic wording remains in player-facing text")
    if "Предмети та золото передано!" not in source:
        fail("simple completion text is missing")

    helpers = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_trade_show_current_stage_12_7_0"
    ]
    if len(helpers) != 1:
        fail("12.7.0b current-stage renderer missing")
    helper_source = ast.get_source_segment(source, helpers[0]) or ""
    if "_trade_editor_text(state)" not in helper_source:
        fail("first-ready refresh does not use canonical editor text")

    registrars = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "register_player_interaction_handlers"
    ]
    if len(registrars) != 1:
        fail("canonical registration count changed")

    print("[OK] Player trade first-ready status and completion-text contracts")
    print("- first ready click renders visible status in the main editor message: OK")
    print("- both participant statuses appear above the reset-warning line: OK")
    print("- status block is rendered exactly once: OK")
    print("- 12.7.0b synchronized current-stage renderer remains connected: OK")
    print("- completion text is simple player-facing wording: OK")
    print("- canonical handler architecture preserved: OK")
    print("- real user/database mutations: 0")


if __name__ == "__main__":
    main()
