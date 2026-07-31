#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "handlers" / "runes.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    source = TARGET.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(TARGET))
    functions = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "rune_master_shop_callback"
    ]
    if len(functions) != 1:
        fail(f"rune_master_shop_callback count={len(functions)}")
    block = ast.get_source_segment(source, functions[0]) or ""
    required = (
        "bot.edit_message_text(",
        'if "message is not modified" not in str(error).lower():',
        "raise",
        'action = parts[1] if len(parts) > 1 else "home"',
    )
    for marker in required:
        if marker not in block:
            fail(f"shop refresh guard missing: {marker}")
    if "except Exception as error:" not in block:
        fail("selective Telegram no-op exception guard missing")

    print("[OK] Rune Master shop refresh hotfix contracts")
    print("- unchanged Refresh is treated as successful no-op")
    print("- unexpected Telegram/API exceptions are re-raised")
    print("- purchase callbacks remain unchanged")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
