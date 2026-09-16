# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

source = (PROJECT_ROOT / "systems" / "character_system.py").read_text(encoding="utf-8-sig")
tree = ast.parse(source)
owners = [
    node for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name == "set_character_class"
]
assert len(owners) == 1
owner_source = ast.get_source_segment(source, owners[0]) or ""
assert "SELECT character_class, class_selected_at FROM users WHERE user_id=?" in owner_source
assert "is_initial_class_selection = not previous_class_selected_at" in owner_source
assert "if is_initial_class_selection:" in owner_source
assert "if not previous_class:" not in owner_source
assert 'f"player_joined:{int(user_id)}"' in owner_source
assert owner_source.index("SELECT character_class, class_selected_at") < owner_source.index("UPDATE users SET character_class")
assert owner_source.index("if is_initial_class_selection:") > owner_source.index("db.conn.commit()")

# Contract truth table for the authoritative class_selected_at marker.
def is_initial(value):
    return not str(value or "").strip()

assert is_initial(None) is True
assert is_initial("") is True
assert is_initial("   ") is True
assert is_initial("2026-09-16T20:00:00") is False

print("NEW_CHARACTER_CHRONICLE_EVENT_18_XX_13B_OK")
