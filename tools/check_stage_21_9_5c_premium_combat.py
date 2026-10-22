#!/usr/bin/env python3
from decimal import Decimal
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.domain.premium_combat import PremiumCombatModifier, PremiumCombatSnapshot
out=PremiumCombatModifier().apply(base_combat_exp=100,base_combat_gold=Decimal("10.00"),premium_active_snapshot=PremiumCombatSnapshot(True))
assert out.exp_final==125 and out.gold_final==Decimal("12.50")
print("STAGE_21_9_5C_PREMIUM_COMBAT_SMOKE: PASS")
