#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.application.post_combat_hooks import PostCombatHookCoordinator, SettledVictoryEvent, CANONICAL_CONSUMER_ORDER
assert PostCombatHookCoordinator and SettledVictoryEvent and len(CANONICAL_CONSUMER_ORDER)==7
print("STAGE_21_9_6C_POST_COMBAT_HOOKS_SMOKE: PASS")
