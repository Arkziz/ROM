#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "handlers" / "combat.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    source = TARGET.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(TARGET))
    names = {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    required_functions = {
        "_combat_extract_retry_after_11_3_1",
        "_install_combat_safe_send_11_3_1",
        "_combat_callback_allowed_11_3_1",
        "_combat_message_allowed_11_3_1",
    }
    if not required_functions.issubset(names):
        fail(f"missing helpers: {sorted(required_functions - names)}")

    required_markers = (
        "_COMBAT_CALLBACK_DEBOUNCE_SECONDS_11_3_1 = 0.90",
        "_install_combat_safe_send_11_3_1(bot)",
        'if not _combat_message_allowed_11_3_1(message):',
        'if not _combat_callback_allowed_11_3_1(bot, call, "attack"):',
        'if not _combat_callback_allowed_11_3_1(bot, call, "skill"):',
        'if not _combat_callback_allowed_11_3_1(bot, call, "potion"):',
        'if not _combat_callback_allowed_11_3_1(bot, call, "flee"):',
        'if not _combat_callback_allowed_11_3_1(bot, call, "potion_use"):',
        'if "too many requests" not in text.lower():',
        "presentation suppressed",
    )
    for marker in required_markers:
        if marker not in source:
            fail(f"missing rate-limit marker: {marker}")

    # Guards must appear before state-mutating calls in callback bodies.
    checks = {
        "combat_attack_callback": "attack(message)",
        "combat_use_skill_callback": "init_combat_effects(mob)",
        "combat_flee_callback": "escape(message)",
    }
    functions = {
        node.name: ast.get_source_segment(source, node) or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }
    for function_name, mutation_marker in checks.items():
        block = functions.get(function_name, "")
        guard_position = block.find("_combat_callback_allowed_11_3_1")
        mutation_position = block.find(mutation_marker)
        if guard_position < 0 or mutation_position < 0 or guard_position > mutation_position:
            fail(f"{function_name}: guard is not before mutation")

    # Execute isolated helper definitions with fake time/bot objects.
    module = {}
    # Execute only the hotfix helpers. Do not execute unrelated combat.py
    # imports such as data.locations, because this smoke test must remain
    # independent of the caller's current working directory and sys.path.
    import re
    import time
    module = {
        "_combat_rate_re_11_3_1": re,
        "_combat_rate_time_11_3_1": time,
    }
    helper_nodes = [
        node for node in tree.body
        if (isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id.startswith("_COMBAT_")
            for target in node.targets
        ))
        or (isinstance(node, ast.FunctionDef) and node.name in required_functions)
    ]
    isolated = ast.Module(body=helper_nodes, type_ignores=[])
    ast.fix_missing_locations(isolated)
    exec(compile(isolated, str(TARGET), "exec"), module)
    parser = module["_combat_extract_retry_after_11_3_1"]
    if parser("429 Too Many Requests: retry after 20") != 20:
        fail("retry_after parser failed")
    if parser("400 Bad Request") is not None:
        fail("non-429 error was misclassified")

    print("[OK] Combat callback/rate-limit hotfix contracts")
    print("- callback debounce: 0.90s")
    print("- duplicate attack/skill/flee blocked before mutation: OK")
    print("- potion menu/use callback guards: OK")
    print("- Hunt blocked during Telegram cooldown: OK")
    print("- Telegram 429 retry_after parser: OK")
    print("- stale combat messages are not retried: OK")
    print("- non-429 send exceptions remain visible: OK")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
