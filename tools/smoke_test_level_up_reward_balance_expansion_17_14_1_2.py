#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
DB=ROOT/"game.db"
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
before=sha(DB)
source=(ROOT/"systems/level_up_reward_system.py").read_text(encoding="utf-8")
ast.parse(source)
assert source.count("ROM 17.14.1.2 LEVEL UP REWARD BALANCE EXPANSION")==1
from systems.level_up_reward_system import calculate_level_rewards
normal=calculate_level_rewards(5,6)
assert normal["gold"]==60
assert normal["small_health_potions"]==3
assert normal["small_mana_potions"]==1
assert normal["refine_stones"]==5
assert normal["medium_health_potions"]==0
assert normal["medium_mana_potions"]==0
milestone=calculate_level_rewards(9,10)
assert milestone["gold"]==300
assert milestone["small_health_potions"]==3
assert milestone["small_mana_potions"]==1
assert milestone["refine_stones"]==5
assert milestone["medium_health_potions"]==2
assert milestone["medium_mana_potions"]==1
multi=calculate_level_rewards(4,7)
assert multi["gold"]==280
assert multi["small_health_potions"]==9
assert multi["small_mana_potions"]==3
assert multi["refine_stones"]==15
assert multi["medium_health_potions"]==2
assert multi["medium_mana_potions"]==1
assert "simple_extractors" not in multi
assert "RUNE_EXTRACTOR_ITEM_ID" not in source
assert "REFINE_STONE_ITEM_ID" in source
assert "commit=False" in source
assert "ROLLBACK TO" in source
assert "items_claimed=0" in source
assert sha(DB)==before
print("[PASS] Stage 17.14.1.2 expanded level-up reward balance contract")
