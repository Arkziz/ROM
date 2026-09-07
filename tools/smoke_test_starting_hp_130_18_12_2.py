from pathlib import Path
import ast
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from data.player_hp import (STARTING_HP_BASE, HP_PER_LEVEL, HP_PER_STAMINA, calculate_base_max_hp, get_starting_max_hp)
assert STARTING_HP_BASE == 60
assert HP_PER_LEVEL == 20
assert HP_PER_STAMINA == 5
assert get_starting_max_hp() == 130
assert calculate_base_max_hp(1, 10) == 130
assert calculate_base_max_hp(3, 12) == 180
for rel, function_name in (("systems/player_system.py", "get_max_hp"), ("systems/notifications.py", "get_worker_max_hp")):
    text = (ROOT / rel).read_text(encoding="utf-8")
    tree = ast.parse(text)
    defs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == function_name]
    assert len(defs) == 1, (rel, function_name, len(defs))
    seg = ast.get_source_segment(text, defs[0]) or ""
    assert "calculate_base_max_hp" in seg
player_text = (ROOT / "db_modules/player.py").read_text(encoding="utf-8")
assert "starting_max_hp = get_starting_max_hp()" in player_text
assert "\n        170,\n        170,\n" not in player_text
print("PASS: canonical starting HP=130; single player/worker formulas; registration uses shared policy")
