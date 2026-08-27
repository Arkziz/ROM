import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for rel in ("handlers/profile.py","systems/profile_history_system.py"):ast.parse((R/rel).read_text(encoding="utf-8"),filename=rel)
sys.path.insert(0,str(R));from systems.profile_history_system import HISTORY_RETENTION_RECORDS_PER_USER,HISTORY_RETENTION_MIN_DAYS,cleanup_history_retention
assert HISTORY_RETENTION_RECORDS_PER_USER==100 and HISTORY_RETENTION_MIN_DAYS==60
assert cleanup_history_retention(preview=True)["preview"] is True
p=(R/"handlers/profile.py").read_text(encoding="utf-8");assert "📜 Історія" in p and "profile_history_trade" in p and "profile_history_pvp" in p
print("[PASS] Stage 17.24.1 profile history contract")
