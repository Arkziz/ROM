#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated contracts for Combat Mana Potion implementation."""
from __future__ import annotations
import ast
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DB_PATH = ROOT / "game.db"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint():
    return hashlib.sha256(DB_PATH.read_bytes()).hexdigest(), DB_PATH.stat().st_size, DB_PATH.stat().st_mtime_ns


def main():
    before = fingerprint()
    from systems import potion_system as potion
    from handlers import combat

    originals = {
        "get_inventory_entry": potion.get_inventory_entry,
        "consume_inventory_item": potion.consume_inventory_item,
        "get_current_hp": potion.get_current_hp,
        "get_max_hp": potion.get_max_hp,
        "set_current_hp": potion.set_current_hp,
        "get_user_mp": potion.get_user_mp,
        "set_user_mp": potion.set_user_mp,
        "get_inventory_detailed": combat.get_inventory_detailed,
        "get_character_profile_summary": combat.get_character_profile_summary,
        "get_item_by_inventory_id_full": combat.get_item_by_inventory_id_full,
    }
    consumed = []
    written_mp = []
    written_hp = []
    entries = {
        1: (1, 202, "🔵 Мале зілля мани", "potion_mp", "potion", 2),
        2: (2, 204, "🔵 Середнє зілля мани", "potion_mp_medium", "potion", 1),
        3: (3, 201, "🔴 Мале зілля здоров’я", "potion_hp", "potion", 2),
    }
    try:
        potion.get_inventory_entry = lambda user_id, inventory_id: entries.get(inventory_id)
        potion.consume_inventory_item = lambda user_id, inventory_id, quantity: consumed.append((inventory_id, quantity)) or True
        potion.get_user_mp = lambda user_id: {"mp": 20, "max_mp": 100}
        potion.set_user_mp = lambda user_id, value: written_mp.append(value)
        potion.get_current_hp = lambda user_id: 50
        potion.get_max_hp = lambda user_id: 170
        potion.set_current_hp = lambda user_id, value: written_hp.append(value)

        small = potion.use_potion_from_inventory(-1, 1)
        if small.get("resource") != "mp" or small.get("restore_mp") != 40 or small.get("new_mp") != 60:
            fail(f"small MP contract failed: {small}")
        medium = potion.use_potion_from_inventory(-1, 2)
        if medium.get("resource") != "mp" or medium.get("restore_mp") != 80 or medium.get("new_mp") != 100:
            fail(f"medium MP clamp failed: {medium}")
        hp = potion.use_potion_from_inventory(-1, 3)
        if hp.get("resource") != "hp" or hp.get("new_hp") != 100 or hp.get("heal") != 50:
            fail(f"HP compatibility failed: {hp}")
        if consumed != [(1, 1), (2, 1), (3, 1)]:
            fail(f"consume exactly once failed: {consumed}")

        before_full = list(consumed)
        potion.get_user_mp = lambda user_id: {"mp": 100, "max_mp": 100}
        full = potion.use_potion_from_inventory(-1, 1)
        if full.get("success") is not False or consumed != before_full:
            fail("full MP must not consume potion")

        # Keyboard visibility and cooldowns.
        items = [
            (1, 202, "MP small", "potion_mp", "common", "potion", 2, 10, 100, 0,0,0,0,0,0,0,1.2),
            (2, 204, "MP medium", "potion_mp_medium", "common", "potion", 1, 10, 100, 0,0,0,0,0,0,0,3.6),
            (3, 201, "HP small", "potion_hp", "common", "potion", 2, 10, 100, 0,0,0,0,0,0,0,1.0),
        ]
        combat.get_inventory_detailed = lambda user_id: items
        combat.get_character_profile_summary = lambda user_id: {"resource_type": "mana"}
        mana_kb = combat.build_combat_potion_kb(-1)
        mana_callbacks = [button.callback_data for row in mana_kb.keyboard for button in row]
        if not {"combat_potion_1", "combat_potion_2", "combat_potion_3"}.issubset(set(mana_callbacks)):
            fail(f"mana keyboard missing potions: {mana_callbacks}")
        combat.get_character_profile_summary = lambda user_id: {"resource_type": "rage"}
        nonmana_kb = combat.build_combat_potion_kb(-1)
        nonmana_callbacks = [button.callback_data for row in nonmana_kb.keyboard for button in row]
        if "combat_potion_1" in nonmana_callbacks or "combat_potion_2" in nonmana_callbacks:
            fail(f"MP potion visible to non-mana class: {nonmana_callbacks}")

        def full_item(type_):
            return (1, 999, "x", type_, "common", "potion", None, 1, 1, 10, 100, 0,0,0,0,0,0,0,1.0)
        for type_, expected in (("potion_mp", 3), ("potion_mp_medium", 5), ("potion_hp", 3), ("potion_hp_medium", 5)):
            combat.get_item_by_inventory_id_full = lambda inventory_id, value=full_item(type_): value
            actual = combat.get_potion_cooldown_turns_by_inventory_id(1)
            if actual != expected:
                fail(f"cooldown {type_}={actual}, expected {expected}")

        combat_source = (ROOT / "handlers" / "combat.py").read_text(encoding="utf-8-sig")
        if 'resource == "mp"' not in combat_source or 'mob["player_mp"]' not in combat_source:
            fail("combat callback MP synchronization missing")
        if "Хід не витрачено" not in combat_source:
            fail("turn-free potion rule missing")
    finally:
        for name, value in originals.items():
            module = potion if hasattr(potion, name) and name in {
                "get_inventory_entry", "consume_inventory_item", "get_current_hp", "get_max_hp",
                "set_current_hp", "get_user_mp", "set_user_mp"
            } else combat
            setattr(module, name, value)

    if before != fingerprint():
        fail("game.db changed during isolated contracts")
    print("[OK] Combat Mana Potion implementation contracts")
    print("- small MP restore: 40")
    print("- medium MP restore/clamp: OK")
    print("- full mana no-consume: OK")
    print("- consume exactly once: OK")
    print("- HP potion compatibility: OK")
    print("- mana-class keyboard visibility: OK")
    print("- non-mana-class hiding: OK")
    print("- cooldown small/medium: 3/5")
    print("- combat MP state synchronization: OK")
    print("- potion use spends no turn: OK")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
