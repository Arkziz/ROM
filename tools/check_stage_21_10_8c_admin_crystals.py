import ast
from pathlib import Path
r=Path(__file__).resolve().parents[1];a=r/"rom_v2/application/admin_crystals.py";t=r/"tests_v2/test_admin_crystals.py"
for p in (a,t):ast.parse(p.read_text(),filename=str(p))
s=a.read_text();required=("class AdminCrystalAdjustmentService","class AdminCrystalAdjustmentCommand","class AdminCrystalAdjustmentReceipt","operation_key_payload_conflict","admin_authorization_required","stale_balance","requested_amount","applied_amount","class AdminCrystalNotification")
m=[x for x in required if x not in s]
if m:raise SystemExit(f"missing_contract_tokens:{m}")
print("STAGE_21_10_8C_ADMIN_CRYSTALS_SMOKE: PASS")
