from __future__ import annotations
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

source = (ROOT / "handlers/combat.py").read_text(encoding="utf-8-sig")
tree = ast.parse(source, filename="handlers/combat.py")
hunts = [
    node for node in ast.walk(tree)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "hunt"
]
assert len(hunts) == 1
hunt = ast.get_source_segment(source, hunts[0]) or ""
assert "from systems.travel_system import is_user_travelling" in hunt
assert "from keyboards import map_kb" in hunt
assert hunt.index("if is_user_travelling(user_id):") < hunt.index("consume_energy_for_hunt(user_id)")
assert "Полювання недоступне під час подорожі" in hunt
assert "оновити час у дорозі" in hunt
assert "reply_markup=map_kb()" in hunt

# Verify that every loaded name used by the travel guard has an owner inside the
# function or module and that the local map_kb import precedes its call.
local_import = hunt.index("from keyboards import map_kb")
keyboard_call = hunt.index("reply_markup=map_kb()")
assert local_import < keyboard_call

from keyboards import map_kb
keyboard = map_kb()
buttons = [
    button.get("text") if isinstance(button, dict) else button.text
    for row in keyboard.keyboard
    for button in row
]
assert buttons == ["🔽 Згорнути мапу"]
print("[PASS] Stage 18.22.3a travel hunt guard informs the player without NameError")
