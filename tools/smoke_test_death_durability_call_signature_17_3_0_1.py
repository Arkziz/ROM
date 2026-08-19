#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "handlers" / "combat.py"


def require(value, message):
    if not value:
        raise AssertionError(message)


def main():
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "damage_equipped_items_on_death":
            calls.append(node)
    require(len(calls) == 3, f"expected three PvE death durability calls, found {len(calls)}")
    for call in calls:
        keywords = {item.arg for item in call.keywords if item.arg}
        require(keywords == {"user_id"}, f"unexpected keywords: {keywords}")
        require(not call.args, "positional arguments are not expected")
    require(source.count("# ROM 17.3.0.1 DEATH DURABILITY CALL SIGNATURE RECOVERY") == 1, "marker count")
    require("amount=5" not in "\n".join(
        ast.get_source_segment(source, call) or "" for call in calls
    ), "legacy amount keyword remains")
    print("[PASS] Stage 17.3.0.1 death durability call signature")


if __name__ == "__main__":
    main()
