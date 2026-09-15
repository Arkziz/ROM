#!/usr/bin/env python3
from __future__ import annotations
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import handlers.combat

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
assert victory.count("🏆 ВИ ПЕРЕМОГЛИ!") == 1
assert victory.count("💥 ФІНАЛЬНИЙ ХІД") == 1
assert victory.find("🏆 ВИ ПЕРЕМОГЛИ!") < victory.find("💥 ФІНАЛЬНИЙ ХІД")
lines = [line for line in victory.splitlines() if "повалений на землю" in line]
assert len(lines) == 1
assert "\\n\\n" not in lines[0].split("повалений на землю", 1)[0]
assert "Нагорода" in victory and "Лут" in victory and "Сумка" in victory
assert "💀 ТИ ЗАГИНУВ" not in victory
assert "💥 ОСТАННІЙ ХІД" in defeat
assert "💥 ОСТАННІ ПОДІЇ БОЮ" not in defeat
print("VICTORY_FINAL_TURN_SPACING_18_XX_3A_OK")
