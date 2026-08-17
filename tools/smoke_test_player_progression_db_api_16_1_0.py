from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from data.player_progression import get_exp_to_next_level as canonical
from db import get_exp_to_next_level as compatibility
for level in (1,2,5,8,10):
    assert compatibility(level)==canonical(level),(level,compatibility(level),canonical(level))
assert compatibility(1)>0
print("[PASS] player progression DB API restored")
