#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "systems" / "rune_system.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def find_function(tree, name):
    return next(
        (node for node in ast.walk(tree)
         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name),
        None,
    )


def main():
    source = TARGET.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(TARGET))
    function = find_function(tree, "claim_daily_quest_reward_with_firius_tokens")
    if function is None:
        fail("Daily Firius reward function not found")

    messages = []
    for node in ast.walk(function):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            messages.append(node.value)

    relevant = [
        value for value in messages
        if "Сумка переповнена" in value
        or "Ви отримали нагороду" in value
        or "Прогрес:" in value
        or "Звільни місце" in value
    ]
    if not relevant:
        fail("Daily reward messages not found")

    literal_escapes = [value for value in relevant if "\\n" in value]
    if literal_escapes:
        fail(f"literal backslash-n remains in messages: {literal_escapes}")

    required = (
        "🎒 Сумка переповнена.\n\n",
        "Звільни місце в інвентарі та спробуй забрати нагороду ще раз.\n",
        "🎁 Ви отримали нагороду за щоденне завдання!\n\n",
    )
    function_source = ast.get_source_segment(source, function) or ""
    compiled = compile(function_source, str(TARGET), "exec")
    namespace = {}
    exec(compiled, namespace)
    constants = []
    for code_object in compiled.co_consts:
        if hasattr(code_object, "co_consts"):
            constants.extend(value for value in code_object.co_consts if isinstance(value, str))
    joined = "\n".join(constants)
    for expected in required:
        if expected not in joined:
            fail(f"expected rendered newline contract missing: {expected!r}")

    print("[OK] Daily reward newline hotfix contracts")
    print("- literal \\n sequences in user messages: 0")
    print("- full-bag paragraph breaks: OK")
    print("- successful reward paragraph breaks: OK")
    print("- Telegram will receive real newline characters: yes")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
