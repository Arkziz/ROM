from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
path=ROOT/"handlers"/"combat.py"
text=path.read_text(encoding="utf-8"); tree=ast.parse(text,filename=str(path))
fn=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="build_victory_text")
src=ast.get_source_segment(text,fn)
assert "final_round_parts.append(clean_prefix)" not in src
assert "last_damage > 0 and not defeated_by_effect" in src
assert "Здоров’я після фінального ходу" in src
assert "смертельну шкоду від ефекту" in src
assert "cooldown_start_text" not in src
assert "player_effects_text" not in src
print("[PASS] simplified final combat summary contract")
