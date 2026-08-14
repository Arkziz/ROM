from __future__ import annotations
import random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from systems.combat_system import generate_mob
from data.bosses import BOSS_ENCOUNTERS_ENABLED
assert BOSS_ENCOUNTERS_ENABLED is False
random.seed(155000)
for level,location in ((1,'start_path'),(5,'start_path'),(6,'dark_forest'),(10,'dark_forest')):
 for _ in range(100):
  mob=generate_mob(level,location)
  assert not mob.get('is_boss')
  assert mob.get('enemy_type') in {'normal','elite'}
print('[PASS] 400 live hunt generations preserve normal/elite behavior while gate is disabled')
