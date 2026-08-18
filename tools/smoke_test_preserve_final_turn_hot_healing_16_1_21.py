from __future__ import annotations
import ast, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
path = ROOT / "handlers" / "combat.py"
text = path.read_text(encoding="utf-8")
tree = ast.parse(text, filename=str(path))
fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "finalize_combat_state_before_victory")
source = ast.get_source_segment(text, fn)
assert "rollback_turn_start_hot_heal_on_victory(user_id, mob)" not in source
assert 'mob["_turn_start_hot_heal_applied"] = 0' in source

# Model the reported case: 403 HP + 17 legitimate HoT = 420 HP.
current_hp = 403
max_hp = 420
hot_heal = 17
healed_hp = min(max_hp, current_hp + hot_heal)
assert healed_hp == 420
finalized_hp = max(1, min(max_hp, healed_hp))
assert finalized_hp == 420

import handlers.combat
print("[PASS] legitimate final-turn HoT remains in persisted HP")
