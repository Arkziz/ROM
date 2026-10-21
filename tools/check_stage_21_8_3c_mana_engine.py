from pathlib import Path
import ast,sys
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.domain.mana_engine import *
assert (MAX_MP_BASE,MAX_MP_PER_LEVEL,MAX_MP_PER_INT,MAX_MP_PER_WIS)==(100,20,1,4)
assert (MANA_POST_COMBAT_FLOOR_PERCENT,MANA_REGEN_PERCENT_PER_FULL_MINUTE)==(50,30)
assert mana_calculate_max_mp(1,0,0)==120
p=R/"rom_v2/domain/mana_engine.py";tree=ast.parse(p.read_text(encoding="utf-8"))
assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and ("infrastructure" in ast.unparse(n) or "presentation" in ast.unparse(n)) for n in ast.walk(tree))
print("[PASS] Stage 21.8.3c canonical mana engine contract")
