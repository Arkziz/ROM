from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
path=ROOT/"handlers"/"combat.py"
text=path.read_text(encoding="utf-8"); tree=ast.parse(text,filename=str(path))
assert text.count('mob["_last_player_damage"] = int(dmg or 0)')>=2
assert '💥 ФІНАЛЬНИЙ ХІД' in text
assert 'Здоров’я після фінального ходу' in text
assert 'last_damage > 0 and "шкоди" not in clean_prefix.lower()' in text
fn=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="build_victory_text")
src=ast.get_source_segment(text,fn)
assert src.index('💥 ФІНАЛЬНИЙ ХІД') < src.index('{victory_title}')
print("[PASS] final combat round summary contract")
