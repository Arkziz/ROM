#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.application.reward_settlement import RewardSettlementCommand, RewardSettlementService
assert RewardSettlementService and RewardSettlementCommand.__dataclass_fields__["operation_key"]
print("STAGE_21_9_3C_REWARD_SETTLEMENT_SMOKE: PASS")
