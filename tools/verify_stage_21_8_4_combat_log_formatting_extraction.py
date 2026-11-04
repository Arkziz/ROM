import ast
from pathlib import Path
combat=Path("handlers/combat.py").read_text(encoding="utf-8-sig")
formatting=Path("handlers/combat_formatting.py").read_text(encoding="utf-8-sig")
ct=ast.parse(combat);ft=ast.parse(formatting)
def count(tree,name):return sum(1 for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
assert count(ct,"build_lethal_combat_log")==0
assert count(ft,"build_lethal_combat_log")==1
assert combat.count("from handlers.combat_formatting import build_lethal_combat_log")==1
assert "from handlers.combat import build_death_text" in formatting
assert "register_combat_handlers" in combat
print("PASS: Stage 21.8.4 canonical combat formatting owner")
