from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from db import get_daily_quest_status,claim_daily_quest_reward
assert callable(get_daily_quest_status)
assert callable(claim_daily_quest_reward)
print("[PASS] daily handler DB API restored")
