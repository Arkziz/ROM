from pathlib import Path
import ast, math, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
from data.player_combat_chances import *
assert calculate_physical_crit_chance(10)==5.0
assert abs(calculate_physical_crit_chance(24.2857142857)-10.0)<1e-6
assert calculate_physical_crit_chance(1000000)==35.0
assert calculate_magical_crit_chance(10)==5.0
assert calculate_dodge_chance(10,10)==5.0
assert calculate_dodge_chance(135,10)==30.0
assert calculate_dodge_chance(10,1000)==1.0
class F:
 def __init__(self,v):self.v=v
 def random(self):return self.v
assert not roll_chance(0,F(0.0))
assert roll_chance(100,F(math.nextafter(1.0,0.0)))
assert not roll_chance(35,F(0.35))
assert roll_chance(35,F(math.nextafter(0.35,0.0)))
for rel,names in {'systems/player_system.py':('get_physical_crit_chance_display','get_magical_crit_chance_display','get_base_dodge_chance_display'),'systems/combat_system.py':('get_physical_crit_chance','get_magical_crit_chance','get_dodge_chance')}.items():
 t=(ROOT/rel).read_text(encoding='utf-8');tree=ast.parse(t)
 for n in names:assert len([x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name==n])==1
mt=(ROOT/'systems/pvp_models.py').read_text(encoding='utf-8');mc=[x for x in ast.parse(mt).body if isinstance(x,ast.ClassDef) and x.name=='PvpActorState'];assert len(mc)==1;assert any(isinstance(x,ast.AnnAssign) and isinstance(x.target,ast.Name) and x.target.id=='dex' for x in mc[0].body)
assert '"dex": total_dex' in (ROOT/'systems/pvp_battle_factory.py').read_text(encoding='utf-8')
assert 'calculate_dodge_chance(defender.dex, attacker.dex)' in (ROOT/'systems/pvp_round_engine.py').read_text(encoding='utf-8')
print('PASS: canonical crit/dodge/RNG; real PvP model owner; default-compatible DEX; duplicates removed')
