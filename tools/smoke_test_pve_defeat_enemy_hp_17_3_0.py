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
    functions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "build_lethal_combat_log"
    ]
    require(len(functions) == 1, "build_lethal_combat_log must be unique")
    function_source = ast.get_source_segment(source, functions[0])
    namespace = {"build_death_text": lambda durability: "DEATH"}
    exec(function_source, namespace)
    build = namespace["build_lethal_combat_log"]

    cases = [
        ({"name": "Звичайний ворог", "hp": 84, "max_hp": 310}, "84/310"),
        ({"name": "Елітний ворог", "hp": 125.6, "max_hp": 500}, "126/500"),
        ({"name": "Бос", "hp": -4, "max_hp": 900, "is_boss": True}, "0/900"),
    ]
    for mob, expected_hp in cases:
        text = build({"mob": mob}, -12, 250, {})
        require(f"👹 Противник: {mob['name']}" in text, "enemy name missing")
        require(f"❤️ Здоров’я противника: {expected_hp}" in text, "enemy HP missing")
        require("DEATH" in text, "death summary missing")

    require(source.count("# ROM 17.3.0 PVE DEFEAT ENEMY HP") == 1, "marker count")
    print("[PASS] Stage 17.3.0 PvE defeat enemy HP formatter")


if __name__ == "__main__":
    main()
