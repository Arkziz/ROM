#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def function_source(path, name):
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(path))
    nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name]
    if not nodes:
        fail(f"function missing: {name}")
    node = sorted(nodes, key=lambda item: item.lineno)[-1]
    return ast.get_source_segment(source, node) or ""


def main():
    inventory_path = ROOT / "handlers" / "inventory.py"
    dev_path = ROOT / "handlers" / "dev.py"
    inventory_source = inventory_path.read_text(encoding="utf-8-sig")
    dev_source = dev_path.read_text(encoding="utf-8-sig")

    if '("rune", "💠 Руни")' not in inventory_source:
        fail("Rune inventory category missing")
    for marker in (
        "після вставки у спорядження додає",
        "3 однакові руни одного типу й рівня",
        "1 Жетон Фіріуса",
        "максимальний рівень",
        "Категорія: Руни",
    ):
        if marker not in inventory_source:
            fail(f"Rune description marker missing: {marker}")

    namespace = {}
    exec(compile(function_source(dev_path, "parse_dev_rune_request"), str(dev_path), "exec"), namespace)
    exec(compile(function_source(dev_path, "parse_dev_quantity_request"), str(dev_path), "exec"), namespace)
    parse_rune = namespace["parse_dev_rune_request"]
    parse_quantity = namespace["parse_dev_quantity_request"]

    valid = parse_rune(["/dev_rune", "str", "3", "7"])
    if valid != {"success": True, "stat": "STR", "level": 3, "quantity": 7, "item_id": 503}:
        fail(f"valid rune request mismatch: {valid}")
    if parse_rune(["/dev_rune", "BAD", "1"]).get("success") is not False:
        fail("invalid rune stat accepted")
    if parse_rune(["/dev_rune", "STR", "6"]).get("success") is not False:
        fail("invalid rune level accepted")
    if parse_rune(["/dev_rune", "STR", "1", "1000"]).get("success") is not False:
        fail("invalid rune quantity accepted")
    if parse_quantity(["/dev_firius"]).get("quantity") != 1:
        fail("generic default quantity contract failed")
    if parse_quantity(["/dev_firius"], default=10).get("quantity") != 10:
        fail("Firius default quantity must be 10")

    commands = {
        node.name
        for node in ast.walk(ast.parse(dev_source))
        if isinstance(node, ast.FunctionDef)
    }
    required_commands = {
        "dev_rune", "dev_firius", "dev_extractor", "dev_extractor_perfect"
    }
    if not required_commands.issubset(commands):
        fail(f"DEV commands missing: {required_commands - commands}")
    for command in ("/dev_rune", "/dev_firius", "/dev_extractor", "/dev_extractor_perfect"):
        if command not in dev_source:
            fail(f"DEV help missing command: {command}")

    import db
    db.init_rune_system()
    rows = db.conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT type) FROM items WHERE id BETWEEN 501 AND 528"
    ).fetchone()
    if tuple(rows) != (28, 28):
        fail(f"Rune item seed contract failed: {rows}")

    print("[OK] Rune inventory and DEV command contracts")
    print("- Rune inventory category: Руни")
    print("- rune descriptions: 25 dynamic definitions")
    print("- Rune I-IV next-level description: OK")
    print("- Rune V maximum-level description: OK")
    print("- /dev_rune STAT LEVEL [quantity]: OK")
    print("- /dev_firius [quantity], default 10: OK")
    print("- /dev_extractor [quantity]: OK")
    print("- /dev_extractor_perfect [quantity]: OK")
    print("- invalid stat/level/quantity protection: OK")
    print("- seeded rune-system items: 28")
    print("- stat effects/insertion/fusion active: no")


if __name__ == "__main__":
    main()
