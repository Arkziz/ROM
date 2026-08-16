from __future__ import annotations
import inspect,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from db import create_daily_contract,abandon_active_contract,get_contract_status,claim_contract_reward
for fn in (create_daily_contract,abandon_active_contract,get_contract_status,claim_contract_reward): assert callable(fn),fn
sig=inspect.signature(create_daily_contract)
assert list(sig.parameters)==["user_id","target_mob_name","target_mob_level","target_kills"]
assert sig.parameters["target_kills"].default is None
print("[PASS] contract handler DB API restored")
