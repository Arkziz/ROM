from pathlib import Path
import ast,sys
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.domain.battle import *
p=R/"rom_v2/domain/battle.py";tree=ast.parse(p.read_text(encoding="utf-8"));imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
assert not any(x and (x.startswith("sqlite") or x.startswith("rom_v2.infrastructure") or x.startswith("rom_v2.presentation")) for x in imports)
assert {x.value for x in BattleStatus}=={"ACTIVE","VICTORY","DEFEAT","ESCAPED","COMPLETED"}
print("[PASS] Stage 21.8.1b pure battle aggregate contract")
