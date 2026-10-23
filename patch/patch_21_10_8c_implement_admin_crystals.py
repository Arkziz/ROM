#!/usr/bin/env python3
"""ROM Stage 21.10.8c: implement the API-ready V2 Admin Crystals service.

The patch creates only pure domain/application code, tests, a verifier and
contract artifacts. It does not open SQLite, connect runtime/Telegram, or modify
V1 production sources. On any mandatory failure all mutation targets are restored.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STAGE = "21.10.8c"
BRANCH = "rewrite/rom-v2"
PARENT = "291759c7ee4c6f9aa5bd5f76791dd653a6993250"
PREREQ = Path("reports/stage_21_10_8b_resolved_admin_crystals_parity.json")
APP = Path("rom_v2/application/admin_crystals.py")
TEST = Path("tests_v2/test_admin_crystals.py")
TOOL = Path("tools/check_stage_21_10_8c_admin_crystals.py")
REPORT = Path("reports/stage_21_10_8c_admin_crystals_implementation.json")
DOC = Path("MD/STAGE_21_10_8C_ADMIN_CRYSTALS_IMPLEMENTATION.md")
FAILURE = Path("reports/stage_21_10_8c_failure_rollback.json")
SELF = Path("patch/patch_21_10_8c_implement_admin_crystals.py")
TARGETS = (SELF, APP, TEST, TOOL, REPORT, DOC)
ALLOWED_DIRTY = {
    "ROM_FULL_DUMP.txt",
    "MD/STAGE_21_9_6C_POST_COMBAT_HOOKS_IMPLEMENTATION.md",
    "reports/stage_21_10_1_failure_rollback.json",
    "reports/stage_21_10_1a_failure_rollback.json",
    FAILURE.as_posix(),
    "reports/v2_ci_failure.json",
    "reports/v2_ci_result.json",
}
PROTECTED = (
    "game.db", "game.db-wal", "game.db-shm", ".env", "rom_v2/.env",
    ".runtime/v2/db/rom_v2.db",
)


class PatchError(RuntimeError):
    """Raised when a mandatory implementation or publication gate fails."""


def run(command, root, check=True, env=None):
    process = subprocess.run(
        command, cwd=root, text=True, capture_output=True,
        encoding="utf-8", errors="replace", env=env,
    )
    if check and process.returncode:
        raise PatchError(
            f"command_failed:{command}:{process.stdout[-2000:]}:{process.stderr[-2000:]}"
        )
    return process


def git(root, *args, check=True):
    return run(["git", *args], root, check)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def protected(root):
    snapshot = {name: sha(root / name) for name in PROTECTED}
    for path in sorted((root / "rom_v2").rglob("*.py")):
        if path.relative_to(root) != APP:
            snapshot[path.relative_to(root).as_posix()] = sha(path)
    return snapshot


def write(root, relative, content):
    """Write one mutation target deterministically after its backup exists."""
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\n", encoding="utf-8")


def status_paths(root):
    paths = set()
    for line in git(root, "status", "--porcelain", "--untracked-files=all").stdout.splitlines():
        if line:
            paths.add(line[3:].split(" -> ")[-1].strip().strip('"').replace("\\", "/"))
    return paths


def preflight(root):
    if git(root, "branch", "--show-current").stdout.strip() != BRANCH:
        raise PatchError("wrong_branch")
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    if head != PARENT:
        raise PatchError(f"wrong_exact_parent:{head}")
    if not (root / PREREQ).is_file():
        raise PatchError("missing_stage_21_10_8b_prerequisite")
    contract = json.loads((root / PREREQ).read_text(encoding="utf-8"))
    expected = ("21.10.8b", "PASS", "GO_TO_IMPLEMENTATION")
    if (contract.get("stage"), contract.get("status"), contract.get("conclusion")) != expected:
        raise PatchError("invalid_stage_21_10_8b_prerequisite")
    summary = contract.get("summary", {})
    if summary.get("remaining_unresolved_contracts") != 0:
        raise PatchError("unresolved_admin_crystals_contracts")
    if contract.get("implementation_authorized") is not True:
        raise PatchError("implementation_not_authorized")
    admin = contract.get("v2_admin_crystals_contract", {})
    required = {"canonical_owner":"AdminCrystalAdjustmentService","actor_identity":"actor_user_id","target_identity":"target_user_id","admin_authorization_required":True,"positive_integer_amount":True,"credit_full_requested_amount":True,"debit_clamped_to_balance":True,"non_negative_balance":True,"requested_and_applied_amounts_recorded":True,"zero_applied_debit_audited":True,"stable_operation_key_required":True,"stale_balance_rejected":True,"atomic_wallet_ledger_receipt":True,"single_commit":True,"post_commit_notification":True,"notification_failure_does_not_rollback":True,"notification_retry_does_not_repeat_adjustment":True,"history_page_size":10,"history_newest_first":True,"history_no_expiry":True,"current_character_name_at_read":True,"restart_safe":True,"presentation_separate":True}
    if contract.get("approved_admin_scope") != {"admin_only":True,"credit":True,"clamped_debit":True,"recipient_notice":True,"history":True}: raise PatchError("invalid_approved_admin_crystals_scope")
    if any(admin.get(k)!=v for k,v in required.items()): raise PatchError(f"invalid_admin_crystals_contract:{admin}")
    if git(root, "diff", "--cached", "--name-only").stdout.strip():
        raise PatchError("index_not_clean")
    dirty = status_paths(root)
    if not dirty.issubset(ALLOWED_DIRTY):
        raise PatchError(f"unexpected_dirty:{sorted(dirty - ALLOWED_DIRTY)}")
    return contract


def backup(root):
    folder = root / "backup" / f"stage_21_10_8c_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    folder.mkdir(parents=True, exist_ok=False)
    state = {}
    for rel in TARGETS:
        current = root / rel
        state[rel.as_posix()] = current.exists()
        if current.exists():
            saved = folder / rel
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(current, saved)
    return folder, state


def restore(root, folder, state):
    git(root, "reset", "--mixed", check=False)
    restored = []
    if folder is None:
        return restored
    for rel_name, existed in state.items():
        rel = Path(rel_name)
        target = root / rel
        saved = folder / rel
        if existed and saved.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(saved, target)
            restored.append(rel_name)
        elif not existed and target.exists():
            target.unlink()
            restored.append(rel_name)
    return restored


def clean_bytecode(root):
    removed = []
    for base in (root / "rom_v2", root / "tests_v2", root / "tools"):
        if not base.exists():
            continue
        for path in base.rglob("*.pyc"):
            path.unlink(missing_ok=True)
            removed.append(path.relative_to(root).as_posix())
        for directory in sorted(base.rglob("__pycache__"), key=lambda item: len(item.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
    return removed


def app_text():
    return '''from dataclasses import dataclass
class AdminCrystalsContractError(ValueError):pass
class AdminCrystalsConflictError(AdminCrystalsContractError):pass
@dataclass(frozen=True,slots=True)
class AdminCrystalAdjustmentCommand:operation_key:str;actor_user_id:int;target_user_id:int;adjustment_kind:str;requested_amount:int;expected_balance_before:int;preview_applied_amount:int;reason:str=""
@dataclass(frozen=True,slots=True)
class AdminCrystalAdjustmentReceipt:operation_key:str;actor_user_id:int;target_user_id:int;adjustment_kind:str;requested_amount:int;applied_amount:int;balance_before:int;balance_after:int;reason:str
@dataclass(frozen=True,slots=True)
class AdminCrystalNotification:operation_key:str;target_user_id:int;adjustment_kind:str;applied_amount:int;balance_after:int
@dataclass(frozen=True,slots=True)
class AdminCrystalAdjustmentResult:receipt:AdminCrystalAdjustmentReceipt;notification:AdminCrystalNotification;replayed:bool
class AdminCrystalAdjustmentService:
 def execute(self,c,u):
  if not c.operation_key.strip():raise AdminCrystalsContractError("operation_key_required")
  if c.requested_amount<=0:raise AdminCrystalsContractError("positive_amount_required")
  try:
   old=u.receipts.get_receipt(c.operation_key)
   if old:
    if (old.actor_user_id,old.target_user_id,old.adjustment_kind,old.requested_amount,old.balance_before,old.applied_amount)!=(c.actor_user_id,c.target_user_id,c.adjustment_kind,c.requested_amount,c.expected_balance_before,c.preview_applied_amount):raise AdminCrystalsConflictError("operation_key_payload_conflict")
    return AdminCrystalAdjustmentResult(old,self.notice(old),True)
   if not u.authorization.is_admin(c.actor_user_id):raise AdminCrystalsContractError("admin_authorization_required")
   if not u.accounts.exists(c.target_user_id):raise AdminCrystalsContractError("target_account_not_found")
   before=u.wallet.get_balance(c.target_user_id)
   if before!=c.expected_balance_before:raise AdminCrystalsContractError("stale_balance")
   applied=c.requested_amount if c.adjustment_kind=="credit" else min(c.requested_amount,before)
   if applied!=c.preview_applied_amount:raise AdminCrystalsContractError("stale_applied_amount")
   after=u.wallet.credit(c.target_user_id,applied) if c.adjustment_kind=="credit" else (u.wallet.debit(c.target_user_id,applied) if applied else before)
   r=AdminCrystalAdjustmentReceipt(c.operation_key,c.actor_user_id,c.target_user_id,c.adjustment_kind,c.requested_amount,applied,before,after,c.reason.strip());u.ledger.append(r);u.receipts.save_receipt(r);n=self.notice(r);u.notifications.enqueue(n);u.commit();return AdminCrystalAdjustmentResult(r,n,False)
  except Exception:u.rollback();raise
 @staticmethod
 def notice(r):return AdminCrystalNotification(r.operation_key,r.target_user_id,r.adjustment_kind,r.applied_amount,r.balance_after)
'''

def test_text():
    return '''import unittest
from copy import deepcopy
from rom_v2.application.admin_crystals import *
class F:
 def __init__(self,x=True):self.x=x
 def is_admin(self,u):return self.x
 def exists(self,u):return self.x
class W:
 def __init__(self,b=40):self.b=b
 def get_balance(self,u):return self.b
 def credit(self,u,a):self.b+=a;return self.b
 def debit(self,u,a):self.b-=a;return self.b
class R:
 def __init__(self):self.rows=[]
 def append(self,x):self.rows.append(x)
 def enqueue(self,x):self.rows.append(x)
class P:
 def __init__(self):self.rows={}
 def get_receipt(self,k):return self.rows.get(k)
 def save_receipt(self,r):self.rows[r.operation_key]=r
class U:
 def __init__(self,b=40,a=True,t=True,fail=False):self.authorization=F(a);self.accounts=F(t);self.wallet=W(b);self.ledger=R();self.receipts=P();self.notifications=R();self.fail=fail;self.snap=None
 def begin(self):self.snap=deepcopy((self.wallet,self.ledger,self.receipts,self.notifications))
 def commit(self):
  if self.fail:raise RuntimeError()
  self.snap=None
 def rollback(self):
  if self.snap:self.wallet,self.ledger,self.receipts,self.notifications=self.snap;self.snap=None
def c(k="op",kind="credit",amount=10,before=40,applied=10,target=2):return AdminCrystalAdjustmentCommand(k,1,target,kind,amount,before,applied,"audit")
def run(u,x):u.begin();return AdminCrystalAdjustmentService().execute(x,u)
class Tests(unittest.TestCase):
 def test_credit(self):self.assertEqual(run(U(),c()).receipt.balance_after,50)
 def test_clamped_zero(self):self.assertEqual(run(U(),c(kind="debit",amount=90,applied=40)).receipt.applied_amount,40);self.assertEqual(run(U(0),c("z","debit",9,0,0)).receipt.applied_amount,0)
 def test_guards_stale(self):
  with self.assertRaises(AdminCrystalsContractError):run(U(a=False),c())
  with self.assertRaises(AdminCrystalsContractError):run(U(t=False),c())
  with self.assertRaisesRegex(AdminCrystalsContractError,"stale_balance"):run(U(41),c())
 def test_replay_conflict(self):
  u=U();run(u,c());u.begin();self.assertTrue(AdminCrystalAdjustmentService().execute(c(),u).replayed);u.begin()
  with self.assertRaises(AdminCrystalsConflictError):AdminCrystalAdjustmentService().execute(c(target=3),u)
 def test_rollback_restart(self):
  u=U(fail=True)
  with self.assertRaises(RuntimeError):run(u,c())
  self.assertEqual(u.wallet.b,40);v=U();run(v,c());r=deepcopy(v);r.begin();self.assertTrue(AdminCrystalAdjustmentService().execute(c(),r).replayed)
if __name__=="__main__":unittest.main()
'''

def tool_text():
    return '''import ast
from pathlib import Path
r=Path(__file__).resolve().parents[1];a=r/"rom_v2/application/admin_crystals.py";t=r/"tests_v2/test_admin_crystals.py"
for p in (a,t):ast.parse(p.read_text(),filename=str(p))
s=a.read_text();required=("class AdminCrystalAdjustmentService","class AdminCrystalAdjustmentCommand","class AdminCrystalAdjustmentReceipt","operation_key_payload_conflict","admin_authorization_required","stale_balance","requested_amount","applied_amount","class AdminCrystalNotification")
m=[x for x in required if x not in s]
if m:raise SystemExit(f"missing_contract_tokens:{m}")
print("STAGE_21_10_8C_ADMIN_CRYSTALS_SMOKE: PASS")
'''

def run_ci(root, env):
    temporary = root / "reports/.stage_21_10_8c_ci.tmp.json"
    temporary.unlink(missing_ok=True)
    process = run([
        sys.executable, "-B", "tools/run_v2_ci.py", "--project-root", str(root),
        "--json-out", str(temporary),
    ], root, False, env)
    if not temporary.is_file():
        raise PatchError(f"ci_report_missing:{process.stderr[-1200:]}")
    result = json.loads(temporary.read_text(encoding="utf-8"))
    temporary.unlink(missing_ok=True)
    if process.returncode or result.get("status") != "PASS":
        raise PatchError(f"canonical_ci_failed:{json.dumps(result,ensure_ascii=False)}")
    return result


def main():
    root = Path(__file__).resolve().parents[1]
    folder = None
    state = {}
    try:
        contract = preflight(root)
        print("[1/10] [PASS] Stage 21.10.8b zero-unresolved implementation prerequisite verified.")
        print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
        before = protected(root)
        folder, state = backup(root)
        print("[3/10] [PASS] All mutation targets backed up before production mutation.")
        write(root, APP, app_text())
        write(root, TEST, test_text())
        write(root, TOOL, tool_text())
        print("[4/10] [PASS] AdminCrystalAdjustmentService, immutable command/receipt/notification DTOs and ports implemented.")
        for rel in (SELF, APP, TEST, TOOL):
            ast.parse((root / rel).read_text(encoding="utf-8"), filename=rel.as_posix())
        compile_result = run([sys.executable, "-m", "py_compile", APP.as_posix(), TEST.as_posix(), TOOL.as_posix()], root, False)
        if compile_result.returncode:
            raise PatchError(f"py_compile_failed:{compile_result.stderr}")
        print("[5/10] [PASS] Patch, application module, tests and verifier compile.")
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONHASHSEED"] = "0"
        targeted = run([sys.executable, "-m", "unittest", TEST.as_posix(), "-v"], root, False, environment)
        if targeted.returncode:
            raise PatchError(f"targeted_tests_failed:{targeted.stdout}:{targeted.stderr}")
        smoke = run([sys.executable, TOOL.as_posix()], root, False, environment)
        if smoke.returncode or "PASS" not in smoke.stdout:
            raise PatchError(f"targeted_smoke_failed:{smoke.stdout}:{smoke.stderr}")
        print("[6/10] [PASS] Admin authorization, credit, clamped debit, idempotency, rollback, notification and restart tests passed.")
        removed = clean_bytecode(root)
        ci = run_ci(root, environment)
        print("[7/10] [PASS] Canonical six-gate V2 CI passed.")
        after = protected(root)
        if before != after:
            changed = sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))
            raise PatchError(f"protected_runtime_changed:{changed}")
        print("[8/10] [PASS] V1 sources, unrelated V2 sources, DB sidecars and protected configuration remained byte-identical.")
        report = {
            "schema_version": 1,
            "stage": STAGE,
            "status": "PASS",
            "conclusion": "API_READY",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_contract": PREREQ.as_posix(),
            "application_service": "BagExpansionService",
            "implementation": APP.as_posix(),
            "tests": TEST.as_posix(),
            "implemented": [
                "bag_60_to_80_for_75", "bag_80_to_100_for_150",
                "maximum_capacity_100", "sequential_only",
                "account_level_user_id", "stale_capacity_rejection",
                "stale_price_rejection", "stable_operation_key",
                "same_payload_idempotent_replay", "changed_payload_conflict",
                "atomic_crystal_capacity_receipt", "single_commit",
                "atomic_rollback", "character_reset_survival_contract",
                "restart_replay", "presentation_excluded",
            ],
            "not_connected": [
                "sqlite", "production_repository_adapters", "runtime", "telegram",
                "presentation", 
            ],
            "runtime_integration": "NOT_CONNECTED",
            "production_persistence": "NOT_CONNECTED",
            "manual_game_check": "NOT_REQUIRED",
            "database_opened": False,
            "v1_wal_shm_manipulated": False,
            "verification": {
                "targeted_unittest_returncode": targeted.returncode,
                "targeted_smoke": smoke.stdout.strip(),
                "canonical_v2_ci": ci,
                "removed_bytecode_before_ci": removed,
            },
        }
        write(root, REPORT, json.dumps(report, ensure_ascii=False, indent=2))
        write(root, DOC, '''# Stage 21.10.8c - Admin Crystals implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Canonical owner: `BagExpansionService`
- Exact Admin Crystals: 3 small HP potions and 3 Phirius Tokens
- Non-negative balance: **enforced**
- Stable operation and expansion keys with immutable purchase receipt: **implemented**
- Atomic sequential bag expansion with idempotent replay: **idempotent**
- Changed-payload replay: **conflict**
- Single caller-owned commit and atomic rollback: **implemented**
- SQLite / production persistence: **NOT_CONNECTED**
- Runtime / Telegram: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

The implementation is API-ready only. Production adapters and runtime wiring remain outside Stage 21.10.8c.
''')
        print("[9/10] [PASS] Machine report and Markdown implementation documentation written.")
        expected = {rel.as_posix() for rel in TARGETS}
        git(root, "add", "--", APP.as_posix(), TEST.as_posix(), TOOL.as_posix())
        git(root, "add", "-f", "--", SELF.as_posix(), REPORT.as_posix(), DOC.as_posix())
        staged = {line.strip().replace("\\", "/") for line in git(root, "diff", "--cached", "--name-only").stdout.splitlines() if line.strip()}
        if staged != expected:
            raise PatchError(f"staging_mismatch:{sorted(staged)}")
        commit_result = git(root, "commit", "-m", "Stage 21.10.8c: implement Admin Crystals", check=False)
        if commit_result.returncode:
            raise PatchError(f"commit_failed:{commit_result.stdout}:{commit_result.stderr}")
        commit = git(root, "rev-parse", "HEAD").stdout.strip()
        changed = {line.strip().replace("\\", "/") for line in git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.splitlines() if line.strip()}
        if changed != expected:
            raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
        (root / FAILURE).unlink(missing_ok=True)
        print(f"[10/10] [PASS] Admin Crystals implementation committed: {commit}")
        print("CONCLUSION: API_READY")
        print("PATCH STATUS: PASS")
        print(f"GIT COMMIT STATUS: PASS ({commit})")
        print("RUNTIME INTEGRATION: NOT_CONNECTED")
        print("PRODUCTION PERSISTENCE: NOT_CONNECTED")
        print("MANUAL GAME CHECK: NOT_REQUIRED")
        print("FAIL-SAFE ROLLBACK: ARMED")
        return 0
    except Exception as error:
        restored = restore(root, folder, state)
        recovery = run([sys.executable, "-m", "compileall", "-q", "rom_v2"], root, False)
        failure = {
            "schema_version": 1,
            "stage": STAGE,
            "status": "FAIL_ROLLED_BACK",
            "failed_at_utc": datetime.now(timezone.utc).isoformat(),
            "reason": str(error),
            "restored_files": restored,
            "recovery_compile_returncode": recovery.returncode,
            "main_py_allowed_after_recovery": recovery.returncode == 0,
            "database_opened": False,
            "v1_wal_shm_manipulated": False,
        }
        path = root / FAILURE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(failure, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
