#!/usr/bin/env python3
from __future__ import annotations
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import handlers.combat as combat

source = (ROOT / "handlers/combat.py").read_text(encoding="utf-8-sig")
tree = ast.parse(source)
owners = {
    node.name: node
    for node in ast.walk(tree)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}

def body(name):
    node = owners[name]
    return "\n".join(source.splitlines()[node.lineno - 1:node.end_lineno])

victory = body("build_victory_text")
defeat = body("build_lethal_combat_log")
death = body("build_death_text")

assert victory.count("🏆 ВИ ПЕРЕМОГЛИ!") == 1
assert victory.count("💥 ФІНАЛЬНИЙ ХІД") == 1
assert victory.find("🏆 ВИ ПЕРЕМОГЛИ!") < victory.find("💥 ФІНАЛЬНИЙ ХІД")
assert "Нагорода" in victory and "Лут" in victory and "Сумка" in victory
assert victory.find("💥 ФІНАЛЬНИЙ ХІД") < victory.find("Нагорода")

assert "💥 ОСТАННІЙ ХІД" in defeat
assert "💥 ОСТАННІ ПОДІЇ БОЮ" not in defeat
assert "death_heading" in defeat and defeat.find("death_heading") < defeat.find("💥 ОСТАННІЙ ХІД")
assert "death_tail" in defeat and defeat.find("💥 ОСТАННІЙ ХІД") < defeat.rfind("death_tail")
assert "💀 ТИ ЗАГИНУВ" in death
assert "Після поразки" in death
assert "build_death_text(durability_damage)" in defeat

print("BATTLE_RESULT_BEFORE_FINAL_TURN_18_XX_3_OK")
