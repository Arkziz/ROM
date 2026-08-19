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
    require(len(functions) == 1, "build_lethal_combat_log must remain unique")
    function_source = ast.get_source_segment(source, functions[0])
    require("Здоров’я перед поразкою" not in function_source, "redundant player HP line remains")
    require("Здоров’я противника" in function_source, "enemy HP line was removed")
    require("Противник:" in function_source, "enemy name line was removed")
    require("build_death_text" in function_source, "death summary call was removed")
    require(source.count("# ROM 17.3.0.2 REMOVE REDUNDANT PLAYER HP BEFORE DEFEAT") == 1, "marker count")

    namespace = {"build_death_text": lambda durability: "DEATH"}
    exec(function_source, namespace)
    text = namespace["build_lethal_combat_log"](
        {"mob": {"name": "Ворог", "hp": 84, "max_hp": 310}},
        0,
        409,
        {},
    )
    require("Здоров’я перед поразкою" not in text, "runtime redundant player HP line remains")
    require("👹 Противник: Ворог" in text, "runtime enemy name missing")
    require("❤️ Здоров’я противника: 84/310" in text, "runtime enemy HP missing")
    require("DEATH" in text, "runtime death summary missing")
    print("[PASS] Stage 17.3.0.2 redundant player HP line removed")


if __name__ == "__main__":
    main()
