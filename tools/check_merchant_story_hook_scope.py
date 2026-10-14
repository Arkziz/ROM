#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PATH = ROOT / "handlers/city.py"
SOURCE = PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE, filename=str(PATH))

def trader_hook(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "send_story_npc_if_present"
        and any(isinstance(arg, ast.Constant) and arg.value == "trader" for arg in node.args)
    )

def one(name):
    rows = [n for n in ast.walk(TREE) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    assert len(rows) == 1
    return rows[0]

builder = one("build_trade_district_text")
handler = one("show_trade_district")
assert not any(trader_hook(n) for n in ast.walk(builder))
hooks = [n for n in ast.walk(handler) if trader_hook(n)]
assert len(hooks) == 1
assert {arg.id for arg in hooks[0].args if isinstance(arg, ast.Name)} >= {"bot", "message"}
sends = [n for n in ast.walk(handler) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "send_message"]
canonical = [n for n in sends if "build_trade_district_text" in (ast.get_source_segment(SOURCE, n) or "")]
assert len(canonical) == 1
assert (canonical[0].end_lineno or canonical[0].lineno) < hooks[0].lineno
compile(SOURCE, str(PATH), "exec")
print("MERCHANT STORY HOOK SCOPE: PASS")
