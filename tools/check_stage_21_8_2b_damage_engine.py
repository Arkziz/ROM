from pathlib import Path
import ast,sys
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.domain.damage_engine import *
assert DAMAGE_DEFENSE_COEFFICIENT==0.5 and MINIMUM_DAMAGE==1 and CRITICAL_DAMAGE_MULTIPLIER==1.5
assert damage_crit_chance(50)==19 and damage_dodge_chance(50,10)==13
p=R/"rom_v2/domain/damage_engine.py";tree=ast.parse(p.read_text(encoding="utf-8"))
assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and "infrastructure" in ast.unparse(n) for n in ast.walk(tree))
print("[PASS] Stage 21.8.2b canonical damage engine contract")
