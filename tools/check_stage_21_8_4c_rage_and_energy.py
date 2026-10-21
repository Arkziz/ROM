from pathlib import Path
import ast,sys
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.domain.combat_resources import *
assert (RAGE_MAX,RAGE_START,RAGE_GAIN_ON_ATTACK,RAGE_GAIN_ON_DAMAGE_TAKEN)==(100,0,15,10)
assert (ENERGY_MAX,ENERGY_START,ENERGY_REGEN_PER_PLAYER_TURN)==(100,100,20)
p=R/"rom_v2/domain/combat_resources.py";tree=ast.parse(p.read_text(encoding="utf-8"))
assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and ("infrastructure" in ast.unparse(n) or "presentation" in ast.unparse(n)) for n in ast.walk(tree))
print("[PASS] Stage 21.8.4c canonical Rage and Energy contracts")
