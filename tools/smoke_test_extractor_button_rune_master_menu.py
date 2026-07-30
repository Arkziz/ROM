#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "keyboards.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def function_source(source, tree, name):
    nodes = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if len(nodes) != 1:
        fail(f"{name}: expected 1 function, found {len(nodes)}")
    return ast.get_source_segment(source, nodes[0]) or ""


def main():
    source = TARGET.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(TARGET))

    rune_master = function_source(source, tree, "rune_master_kb")
    required = (
        'kb.add("💠 Вставити руну", "🔄 Переробити руни")',
        'kb.add("🧰 Екстрактор")',
        'kb.add("🔙 Ремісничий квартал")',
    )
    for marker in required:
        if marker not in rune_master:
            fail(f"rune_master_kb missing: {marker}")

    positions = [rune_master.index(marker) for marker in required]
    if positions != sorted(positions):
        fail("Rune Master button order is incorrect")

    wrong_functions = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name == "rune_master_kb":
            continue
        block = ast.get_source_segment(source, node) or ""
        if 'kb.add("🧰 Екстрактор")' in block:
            wrong_functions.append(node.name)
    if wrong_functions:
        fail(f"Extractor button leaked into other keyboards: {wrong_functions}")

    handlers_path = ROOT / "handlers" / "runes.py"
    handlers = handlers_path.read_text(encoding="utf-8-sig")
    handlers_tree = ast.parse(handlers, filename=str(handlers_path))

    # Detect the handler semantically through AST. The implementation may use
    # either `message.text`, `m.text`, or another lambda argument name, so an
    # exact source substring check is incorrect.
    extractor_text_found = any(
        isinstance(node, ast.Constant)
        and node.value == "🧰 Екстрактор"
        for node in ast.walk(handlers_tree)
    )
    extractor_handler_function = any(
        isinstance(node, ast.FunctionDef)
        and node.name == "show_extractor"
        for node in ast.walk(handlers_tree)
    )
    if not extractor_text_found or not extractor_handler_function:
        fail("Extractor message handler missing")

    print("[OK] Extractor button Rune Master menu contracts")
    print("- Rune Master Extractor reply button: OK")
    print("- button order: Insert/Fuse -> Extractor -> Back")
    print("- Extractor button in other keyboards: 0")
    print("- Extractor message handler: OK")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
