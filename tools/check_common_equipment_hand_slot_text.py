#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "handlers/city.py"
SOURCE = PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE, filename=str(PATH))
MATCHES = [n for n in ast.walk(TREE) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "build_common_equipment_slot_choice_text"]
assert len(MATCHES) == 1
SEGMENT = ast.get_source_segment(SOURCE, MATCHES[0])
assert SEGMENT
assert "{float(title):.2f}" not in SEGMENT
assert "{float(description):.2f}" not in SEGMENT
assert SEGMENT.count("{title}") >= 1
assert SEGMENT.count("{description}") >= 1
assert SEGMENT.count("{float(gold):.2f}") == 1
assert "🗡️ Вибір зброї" in SEGMENT
assert "🛡️ Вибір другої руки" in SEGMENT
assert "Доступні варіанти:" in SEGMENT
compile(SOURCE, str(PATH), "exec")
print("COMMON EQUIPMENT HAND SLOT TEXT: PASS")
