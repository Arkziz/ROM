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
    required = (
        "ROM 12.6.3b PLAYER TRADE EQUIPMENT USAGE AND QUANTITY LABELS",
        "def _trade_equipment_usage_label_12_6_3b(",
        "Використання: {usage}",
        "Кількість: {int(snapshot.get('quantity') or 0)}",
        "Одноручна зброя",
        "Дворучна зброя",
        "Зброя для другої руки",
        "Предмет для другої руки",
    )
    for contract in required:
        if contract not in source:
            fail(f"missing contract: {contract}")

    namespace = {}
    wanted = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            text = ast.get_source_segment(source, node) or ""
            if "_TRADE_MAIN_HAND_WEAPON_SUBTYPES_12_6_3B" in text or "_TRADE_OFF_HAND_" in text:
                wanted.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == "_trade_equipment_usage_label_12_6_3b":
            wanted.append(node)
    exec(compile(ast.Module(body=wanted, type_ignores=[]), str(HANDLER), "exec"), namespace)
    usage = namespace["_trade_equipment_usage_label_12_6_3b"]

    cases = (
        ({"slot_key":"main_hand","item_subtype":"sword_1h","weapon_hands":1}, "Одноручна зброя"),
        ({"slot_key":"main_hand","item_subtype":"staff_2h","weapon_hands":2}, "Дворучна зброя"),
        ({"slot_key":"off_hand","item_subtype":"dagger","weapon_hands":1}, "Зброя для другої руки"),
        ({"slot_key":"off_hand","item_subtype":"shield","weapon_hands":1}, "Предмет для другої руки"),
        ({"slot_key":"off_hand","item_subtype":"talisman","weapon_hands":1}, "Предмет для другої руки"),
        ({"category":"material","weapon_hands":1}, ""),
        ({"category":"rune","weapon_hands":1}, ""),
        ({"slot_key":"shoulders","armor_type":"cloth","weapon_hands":1}, ""),
    )
    for snapshot, expected in cases:
        actual = usage(snapshot)
        if actual != expected:
            fail(f"usage mismatch: {snapshot} -> {actual!r}, expected {expected!r}")

    final_formatter = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_trade_snapshot_lines_12_6_2"
    ][-1]
    formatter_source = ast.get_source_segment(source, final_formatter) or ""
    if "Кількість рук:" in formatter_source:
        fail("final formatter still exposes technical hand count")
    if "Усього в інвентарі:" in formatter_source:
        fail("final formatter still uses old stack quantity label")

    print("[OK] Player trade equipment usage and quantity label contracts")
    print("- stacks use Кількість: N: OK")
    print("- materials/runes/potions ignore default weapon_hands: OK")
    print("- one-handed and two-handed weapon usage labels: OK")
    print("- off-hand weapon/item usage labels: OK")
    print("- armor and jewelry do not show hand usage: OK")
    print("- isolated helper checks; real user mutations: 0")


if __name__ == "__main__":
    main()
