#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contracts for shared potion cooldown menu UX."""
from __future__ import annotations
import ast
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DB_PATH = ROOT / "game.db"
COMBAT_PATH = ROOT / "handlers" / "combat.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint():
    return (
        hashlib.sha256(DB_PATH.read_bytes()).hexdigest(),
        DB_PATH.stat().st_size,
        DB_PATH.stat().st_mtime_ns,
    )


def main():
    before = fingerprint()
    source = COMBAT_PATH.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(COMBAT_PATH))
    names = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name in {
            "format_combat_turns_uk",
            "build_combat_potion_kb",
            "choose_potion_in_combat",
            "use_selected_potion_in_combat",
        }
    }
    if len(names) != 4:
        fail(f"required function set incomplete: {sorted(names)}")

    choose_source = ast.get_source_segment(source, names["choose_potion_in_combat"]) or ""
    use_source = ast.get_source_segment(source, names["use_selected_potion_in_combat"]) or ""
    if "if cooldown > 0" in choose_source:
        fail("potion menu is still blocked before rendering")
    if "build_combat_potion_kb(user_id, cooldown=cooldown)" not in choose_source:
        fail("potion menu does not receive shared cooldown")
    if "if cooldown > 0" not in use_source:
        fail("potion use callback no longer blocks use during cooldown")
    if "format_combat_turns_uk(cooldown)" not in use_source:
        fail("use callback does not use Ukrainian turn pluralization")

    from handlers import combat

    expected = {
        0: "0 ходів",
        1: "1 хід",
        2: "2 ходи",
        3: "3 ходи",
        4: "4 ходи",
        5: "5 ходів",
        11: "11 ходів",
        12: "12 ходів",
        21: "21 хід",
        22: "22 ходи",
    }
    for value, text in expected.items():
        actual = combat.format_combat_turns_uk(value)
        if actual != text:
            fail(f"pluralization {value}: {actual!r}, expected {text!r}")

    original_inventory = combat.get_inventory_detailed
    original_profile = combat.get_character_profile_summary
    try:
        combat.get_inventory_detailed = lambda user_id: [
            (1, 201, "🔴 Мале зілля здоров’я", "potion_hp", "common", "potion", 3, 10, 100, 0,0,0,0,0,0,0,1.0),
            (2, 202, "🔵 Мале зілля мани", "potion_mp", "common", "potion", 2, 10, 100, 0,0,0,0,0,0,0,1.2),
        ]
        combat.get_character_profile_summary = lambda user_id: {"resource_type": "mana"}
        kb = combat.build_combat_potion_kb(-1, cooldown=3)
        texts = [button.text for row in kb.keyboard for button in row]
        if "⏳ 🔴 Мале зілля здоров’я x3, доступно через 3 ходи" not in texts:
            fail(f"HP cooldown label missing: {texts}")
        if "⏳ 🔵 Мале зілля мани x2, доступно через 3 ходи" not in texts:
            fail(f"MP cooldown label missing: {texts}")
        if "⬅️ Назад до бою" not in texts:
            fail("back button missing")

        combat.get_character_profile_summary = lambda user_id: {"resource_type": "rage"}
        nonmana = combat.build_combat_potion_kb(-1, cooldown=3)
        nonmana_texts = [button.text for row in nonmana.keyboard for button in row]
        if any("зілля мани" in text for text in nonmana_texts):
            fail(f"MP potion visible to non-mana class: {nonmana_texts}")
    finally:
        combat.get_inventory_detailed = original_inventory
        combat.get_character_profile_summary = original_profile

    if before != fingerprint():
        fail("game.db changed during isolated contracts")

    print("[OK] Combat potion cooldown menu UX contracts")
    print("- shared HP/MP cooldown: preserved")
    print("- menu opens during cooldown: OK")
    print("- individual potion callbacks remain blocked: OK")
    print("- cooldown shown on each potion button: OK")
    print("- Ukrainian 1/2/3/4/5 turn forms: OK")
    print("- MP potions hidden from non-mana classes: OK")
    print("- back-to-combat action: preserved")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
