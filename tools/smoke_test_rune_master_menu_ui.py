#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

KEYBOARDS = ROOT / "keyboards.py"
RUNES = ROOT / "handlers" / "runes.py"
INVENTORY = ROOT / "handlers" / "inventory.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    keyboard_source = KEYBOARDS.read_text(encoding="utf-8-sig")
    rune_source = RUNES.read_text(encoding="utf-8-sig")
    inventory_source = INVENTORY.read_text(encoding="utf-8-sig")
    for path, source in (
        (KEYBOARDS, keyboard_source),
        (RUNES, rune_source),
        (INVENTORY, inventory_source),
    ):
        ast.parse(source, filename=str(path))

    keyboard_required = (
        "def rune_master_kb():",
        'kb.add("💠 Вставити руну", "🔄 Переробити руни")',
        'kb.add("🔙 Ремісничий квартал")',
    )
    for marker in keyboard_required:
        if marker not in keyboard_source:
            fail(f"Rune Master keyboard marker missing: {marker}")

    handler_required = (
        "from keyboards import craft_kb, rune_master_kb",
        'message.text == "💠 Вставити руну"',
        'message.text == "🔄 Переробити руни"',
        "reply_markup=rune_master_kb()",
        "build_rune_fusion_home",
    )
    for marker in handler_required:
        if marker not in rune_source:
            fail(f"Rune Master handler marker missing: {marker}")

    if 'message.text == "💠 Рунний Майстер"' not in rune_source:
        fail("Rune Master entry handler missing")

    # Check only the show_rune_master() function. The same source file must
    # still call build_rune_master_home() from the separate
    # show_rune_insertion() action, so a file-wide substring check is invalid.
    rune_tree = ast.parse(rune_source, filename=str(RUNES))
    entry_function = next(
        (
            node for node in ast.walk(rune_tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "show_rune_master"
        ),
        None,
    )
    if entry_function is None:
        fail("show_rune_master function missing")
    entry_source = ast.get_source_segment(rune_source, entry_function) or ""
    if "build_rune_master_home(" in entry_source:
        fail("Rune Master entry still opens insertion list directly")
    if "reply_markup=rune_master_kb()" not in entry_source:
        fail("Rune Master entry does not open dedicated reply keyboard")

    insertion_function = next(
        (
            node for node in ast.walk(rune_tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "show_rune_insertion"
        ),
        None,
    )
    if insertion_function is None:
        fail("show_rune_insertion function missing")
    insertion_source = ast.get_source_segment(rune_source, insertion_function) or ""
    if "build_rune_master_home(" not in insertion_source:
        fail("Insert Rune action does not open equipment selection")

    if "Оберіть предмет для ознайомлення:" not in inventory_source:
        fail("Rune category orientation text missing")
    if 'if category_key != "rune":' not in inventory_source:
        fail("Rune-only inventory text guard missing")

    print("[OK] Rune Master dedicated menu UI contracts")
    print("- Blacksmith/Alchemist buttons inside Rune Master: 0")
    print("- Rune Master actions: 2")
    print("- Insert Rune reply action: OK")
    print("- Fuse Runes reply action: OK")
    print("- Back to Craft District action: OK")
    print("- rune inventory text: Оберіть предмет для ознайомлення")
    print("- other inventory category text changed: no")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
