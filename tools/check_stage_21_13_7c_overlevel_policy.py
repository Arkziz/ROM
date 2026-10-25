from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.application.overlevel_policy_service import *
q=[OverlevelQuestDefinition(f"q{n}",n,"start_path" if n<=50 else "dark_forest") for n in range(1,101)]
u=InMemoryOverlevelUnitOfWork();s=OverlevelPolicyService(u,q)
assert s.reconcile(1,5).changed==0
assert s.reconcile(1,6).changed==50
assert s.reconcile(1,6).changed==0
assert s.reconcile(1,11).changed==50
assert len(u.rows[1])==100
print("Stage 21.13.7c Overlevel policy smoke: PASS")
