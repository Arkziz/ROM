#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import sqlite3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
source_path = ROOT / "systems/player_system.py"
source = source_path.read_text(encoding="utf-8-sig")
tree = ast.parse(source)
definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "add_exp"]
assert len(definitions) == 1, f"canonical add_exp definitions={len(definitions)}, expected 1"
segment = ast.get_source_segment(source, definitions[0]) or ""
assert "free_attribute_points" in segment
assert "total_attribute_points_earned" in segment
assert "attribute_points_awarded = level_ups * 5" in segment
assert "str=str+?" not in segment
assert "str = str + 1" not in segment
facade_source = (ROOT / "db_modules/player.py").read_text(encoding="utf-8-sig")
facade_tree = ast.parse(facade_source)
wrappers = [n for n in facade_tree.body if isinstance(n, ast.FunctionDef) and n.name == "add_exp"]
assert len(wrappers) == 1
wrapper_segment = ast.get_source_segment(facade_source, wrappers[0]) or ""
assert "_player_system().add_exp" in wrapper_segment
conn = sqlite3.connect((ROOT / "game.db").resolve().as_uri() + "?mode=ro", uri=True)
try:
    assert conn.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    assert not list(conn.execute("PRAGMA foreign_key_check"))
finally:
    conn.close()
print("[PASS] Stage 18.16.2 canonical level-up contract")
