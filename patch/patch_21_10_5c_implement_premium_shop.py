#!/usr/bin/env python3
"""ROM Stage 21.10.5c: implement the API-ready V2 Premium Shop service.

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

STAGE = "21.10.5c"
BRANCH = "rewrite/rom-v2"
PARENT = "903cf65b35b5fda3fefdce1468748d9273f93511"
PREREQ = Path("reports/stage_21_10_5b_resolved_premium_shop_parity.json")
APP = Path("rom_v2/application/premium_shop.py")
TEST = Path("tests_v2/test_premium_shop.py")
TOOL = Path("tools/check_stage_21_10_5c_premium_shop.py")
REPORT = Path("reports/stage_21_10_5c_premium_shop_implementation.json")
DOC = Path("MD/STAGE_21_10_5C_PREMIUM_SHOP_IMPLEMENTATION.md")
FAILURE = Path("reports/stage_21_10_5c_failure_rollback.json")
SELF = Path("patch/patch_21_10_5c_implement_premium_shop.py")
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
        raise PatchError("missing_stage_21_10_5b_prerequisite")
    contract = json.loads((root / PREREQ).read_text(encoding="utf-8"))
    expected = ("21.10.5b", "PASS", "GO_TO_IMPLEMENTATION")
    if (contract.get("stage"), contract.get("status"), contract.get("conclusion")) != expected:
        raise PatchError("invalid_stage_21_10_5b_prerequisite")
    summary = contract.get("summary", {})
    if summary.get("remaining_unresolved_contracts") != 0:
        raise PatchError("unresolved_premium_shop_contracts")
    if contract.get("implementation_authorized") is not True:
        raise PatchError("implementation_not_authorized")
    premium = contract.get("v2_premium_shop_contract", {})
    required = {
        "canonical_owner": "PremiumShopService", "account_identity": "user_id",
        "plan_15_key": "premium_15d", "plan_15_days": 15,
        "plan_15_price_crystals": 100, "plan_30_key": "premium_30d",
        "plan_30_days": 30, "plan_30_price_crystals": 180,
        "utc_expiry": True, "inactive_base_now": True,
        "active_base_existing_expiry": True,
        "stable_operation_key_required": True,
        "atomic_crystal_expiry_receipt": True,
        "character_reset_survival": True, "restart_safe": True,
        "caller_owned_unit_of_work": True, "single_commit": True,
        "presentation_separate": True,
    }
    if any(premium.get(key) != value for key, value in required.items()):
        raise PatchError(f"invalid_premium_shop_contract:{premium}")
    if git(root, "diff", "--cached", "--name-only").stdout.strip():
        raise PatchError("index_not_clean")
    dirty = status_paths(root)
    if not dirty.issubset(ALLOWED_DIRTY):
        raise PatchError(f"unexpected_dirty:{sorted(dirty - ALLOWED_DIRTY)}")
    return contract


def backup(root):
    folder = root / "backup" / f"stage_21_10_5c_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
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
    return '''"""Pure API-ready Premium Shop service for ROM V2."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

class PremiumShopContractError(ValueError): pass
class PremiumShopConflictError(PremiumShopContractError): pass

@dataclass(frozen=True, slots=True)
class PremiumPlan:
    plan_key:str
    duration_days:int
    price_crystals:int

PREMIUM_PLANS={
    "premium_15d":PremiumPlan("premium_15d",15,100),
    "premium_30d":PremiumPlan("premium_30d",30,180),
}

@dataclass(frozen=True, slots=True)
class PremiumPurchaseCommand:
    operation_key:str
    user_id:int
    plan_key:str
    quoted_price_crystals:int

@dataclass(frozen=True, slots=True)
class PremiumPurchaseReceipt:
    operation_key:str
    user_id:int
    plan_key:str
    price_crystals:int
    previous_expiry:datetime|None
    base_expiry:datetime
    new_expiry:datetime
    crystal_balance_after:int

@dataclass(frozen=True, slots=True)
class PremiumPurchaseResult:
    receipt:PremiumPurchaseReceipt
    replayed:bool

class PremiumAccountPort(Protocol):
    def get_expiry(self,user_id:int)->datetime|None: ...
    def set_expiry(self,user_id:int,expiry:datetime)->None: ...
class PremiumCrystalWalletPort(Protocol):
    def get_balance(self,user_id:int)->int: ...
    def debit(self,user_id:int,amount:int)->int: ...
class PremiumReceiptPort(Protocol):
    def get_receipt(self,operation_key:str)->PremiumPurchaseReceipt|None: ...
    def save_receipt(self,receipt:PremiumPurchaseReceipt)->None: ...
class PremiumClockPort(Protocol):
    def now_utc(self)->datetime: ...
class PremiumShopUnitOfWorkPort(Protocol):
    account:PremiumAccountPort
    wallet:PremiumCrystalWalletPort
    receipts:PremiumReceiptPort
    clock:PremiumClockPort
    def commit(self)->None: ...
    def rollback(self)->None: ...

class PremiumShopService:
    """Canonical owner for atomic account-level Premium activation and extension."""
    def purchase(self,command:PremiumPurchaseCommand,uow:PremiumShopUnitOfWorkPort)->PremiumPurchaseResult:
        self._validate_command(command)
        try:
            existing=uow.receipts.get_receipt(command.operation_key)
            if existing is not None:
                if not self._same_payload(existing,command):raise PremiumShopConflictError("operation_key_payload_conflict")
                return PremiumPurchaseResult(existing,True)
            plan=PREMIUM_PLANS.get(command.plan_key)
            if plan is None:raise PremiumShopContractError("unknown_premium_plan")
            if command.quoted_price_crystals!=plan.price_crystals:raise PremiumShopContractError("stale_plan_price")
            now=self._utc(uow.clock.now_utc(),"clock_must_return_aware_utc")
            previous=uow.account.get_expiry(command.user_id)
            if previous is not None:previous=self._utc(previous,"stored_expiry_must_be_aware_utc")
            base=previous if previous is not None and previous>now else now
            new_expiry=base+timedelta(days=plan.duration_days)
            if uow.wallet.get_balance(command.user_id)<plan.price_crystals:raise PremiumShopContractError("insufficient_crystals")
            balance_after=uow.wallet.debit(command.user_id,plan.price_crystals)
            uow.account.set_expiry(command.user_id,new_expiry)
            receipt=PremiumPurchaseReceipt(command.operation_key,command.user_id,plan.plan_key,plan.price_crystals,previous,base,new_expiry,balance_after)
            uow.receipts.save_receipt(receipt);uow.commit()
            return PremiumPurchaseResult(receipt,False)
        except Exception:
            uow.rollback();raise
    @staticmethod
    def _validate_command(command:PremiumPurchaseCommand)->None:
        if not command.operation_key.strip():raise PremiumShopContractError("operation_key_required")
        if command.user_id<=0:raise PremiumShopContractError("user_id_must_be_positive")
        if not command.plan_key.strip():raise PremiumShopContractError("plan_key_required")
        if not isinstance(command.quoted_price_crystals,int) or isinstance(command.quoted_price_crystals,bool) or command.quoted_price_crystals<=0:raise PremiumShopContractError("invalid_quoted_price")
    @staticmethod
    def _utc(value:datetime,reason:str)->datetime:
        if value.tzinfo is None or value.utcoffset() is None:raise PremiumShopContractError(reason)
        return value.astimezone(timezone.utc)
    @staticmethod
    def _same_payload(receipt:PremiumPurchaseReceipt,command:PremiumPurchaseCommand)->bool:
        return receipt.user_id==command.user_id and receipt.plan_key==command.plan_key and receipt.price_crystals==command.quoted_price_crystals
'''


def test_text():
    return '''import unittest
from copy import deepcopy
from datetime import datetime,timezone,timedelta
from rom_v2.application.premium_shop import *
NOW=datetime(2026,1,1,tzinfo=timezone.utc)
class Account:
 def __init__(self,e=None):self.expiry=e
 def get_expiry(self,u):return self.expiry
 def set_expiry(self,u,e):self.expiry=e
class Wallet:
 def __init__(self,b=500):self.b=b
 def get_balance(self,u):return self.b
 def debit(self,u,a):
  if self.b<a:raise PremiumShopContractError("insufficient_crystals")
  self.b-=a;return self.b
class Receipts:
 def __init__(self):self.rows={}
 def get_receipt(self,k):return self.rows.get(k)
 def save_receipt(self,r):self.rows[r.operation_key]=r
class Clock:
 def __init__(self,n=NOW):self.n=n
 def now_utc(self):return self.n
class Uow:
 def __init__(self,b=500,e=None,fail=False):self.account=Account(e);self.wallet=Wallet(b);self.receipts=Receipts();self.clock=Clock();self.fail=fail;self.commits=0;self.rollbacks=0;self.snap=None
 def begin(self):self.snap=deepcopy((self.account,self.wallet,self.receipts,self.clock))
 def commit(self):
  if self.fail:raise RuntimeError("commit_failure")
  self.commits+=1;self.snap=None
 def rollback(self):
  self.rollbacks+=1
  if self.snap:self.account,self.wallet,self.receipts,self.clock=self.snap;self.snap=None
def cmd(k="op",plan="premium_15d",price=100):return PremiumPurchaseCommand(k,1,plan,price)
def execute(u,c):u.begin();return PremiumShopService().purchase(c,u)
class Tests(unittest.TestCase):
 def test_activate_15_day_plan(self):
  u=Uow();r=execute(u,cmd());self.assertEqual(r.receipt.new_expiry,NOW+timedelta(days=15));self.assertEqual(u.wallet.b,400);self.assertEqual(u.commits,1)
 def test_activate_30_day_plan(self):
  u=Uow();r=execute(u,cmd(plan="premium_30d",price=180));self.assertEqual(r.receipt.new_expiry,NOW+timedelta(days=30));self.assertEqual(u.wallet.b,320)
 def test_extend_from_active_expiry(self):
  old=NOW+timedelta(days=5);u=Uow(e=old);r=execute(u,cmd());self.assertEqual(r.receipt.base_expiry,old);self.assertEqual(r.receipt.new_expiry,old+timedelta(days=15))
 def test_expired_activates_from_now(self):
  old=NOW-timedelta(seconds=1);u=Uow(e=old);r=execute(u,cmd());self.assertEqual(r.receipt.base_expiry,NOW)
 def test_stale_price_and_unknown_plan_fail_closed(self):
  for c,reason in ((cmd(price=101),"stale_plan_price"),(cmd(plan="other"),"unknown_premium_plan")):
   u=Uow()
   with self.subTest(reason=reason),self.assertRaisesRegex(PremiumShopContractError,reason):execute(u,c)
   self.assertEqual(u.wallet.b,500);self.assertIsNone(u.account.expiry)
 def test_insufficient_crystals(self):
  u=Uow(b=99)
  with self.assertRaisesRegex(PremiumShopContractError,"insufficient_crystals"):execute(u,cmd())
  self.assertIsNone(u.account.expiry)
 def test_replay_and_conflict(self):
  u=Uow();first=execute(u,cmd());u.begin();again=PremiumShopService().purchase(cmd(),u);self.assertTrue(again.replayed);self.assertEqual(first.receipt,again.receipt);self.assertEqual(u.wallet.b,400);u.begin()
  with self.assertRaises(PremiumShopConflictError):PremiumShopService().purchase(cmd(plan="premium_30d",price=180),u)
 def test_commit_failure_rolls_back_all(self):
  u=Uow(fail=True)
  with self.assertRaisesRegex(RuntimeError,"commit_failure"):execute(u,cmd())
  self.assertEqual(u.wallet.b,500);self.assertIsNone(u.account.expiry);self.assertFalse(u.receipts.rows)
 def test_restart_replay(self):
  first=Uow();original=execute(first,cmd());second=deepcopy(first);second.begin();replay=PremiumShopService().purchase(cmd(),second);self.assertTrue(replay.replayed);self.assertEqual(replay.receipt,original.receipt);self.assertEqual(second.account.expiry,NOW+timedelta(days=15))
if __name__=="__main__":unittest.main()
'''


def tool_text():
    return '''#!/usr/bin/env python3
"""Targeted Stage 21.10.5c Premium Shop verifier."""
import ast
from pathlib import Path

root=Path(__file__).resolve().parents[1]
app=root/"rom_v2/application/premium_shop.py"
test=root/"tests_v2/test_premium_shop.py"
for path in (app,test): ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
source=app.read_text(encoding="utf-8")
required=("class PremiumShopService","class PremiumPurchaseCommand","class PremiumPurchaseReceipt","operation_key_payload_conflict","stale_plan_price","insufficient_crystals")
missing=[token for token in required if token not in source]
if missing: raise SystemExit(f"missing_contract_tokens:{missing}")
for forbidden in ("sqlite3","aiogram","telegram"):
    if forbidden in source.lower(): raise SystemExit(f"forbidden_dependency:{forbidden}")
print("STAGE_21_10_5C_PREMIUM_SHOP_SMOKE: PASS")
'''


def run_ci(root, env):
    temporary = root / "reports/.stage_21_10_5c_ci.tmp.json"
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
        print("[1/10] [PASS] Stage 21.10.5b zero-unresolved implementation prerequisite verified.")
        print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
        before = protected(root)
        folder, state = backup(root)
        print("[3/10] [PASS] All mutation targets backed up before production mutation.")
        write(root, APP, app_text())
        write(root, TEST, test_text())
        write(root, TOOL, tool_text())
        print("[4/10] [PASS] PremiumShopService, immutable plan/command/receipt DTOs and ports implemented.")
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
        print("[6/10] [PASS] Fixed 15/30-day plans, UTC activation/extension, idempotency, rollback and restart tests passed.")
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
            "application_service": "PremiumShopService",
            "implementation": APP.as_posix(),
            "tests": TEST.as_posix(),
            "implemented": [
                "fixed_plan_premium_15d_100", "fixed_plan_premium_30d_180",
                "account_level_user_id", "timezone_aware_utc_expiry",
                "inactive_activation_from_now", "active_extension_from_expiry",
                "stable_operation_key", "same_payload_idempotent_replay",
                "changed_payload_conflict", "stale_plan_price_rejection",
                "atomic_crystal_expiry_receipt", "single_commit", "atomic_rollback",
                "restart_replay", "character_reset_survival_contract",
                "presentation_excluded",
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
        write(root, DOC, '''# Stage 21.10.5c - Premium Shop implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Canonical owner: `PremiumShopService`
- Fixed Premium plans: 15 days/100 crystals and 30 days/180 crystals
- Non-negative balance: **enforced**
- Stable operation key and immutable UTC expiry receipt: **implemented**
- Atomic Premium activation/extension with idempotent replay: **idempotent**
- Changed-payload replay: **conflict**
- Single caller-owned commit and atomic rollback: **implemented**
- SQLite / production persistence: **NOT_CONNECTED**
- Runtime / Telegram: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

The implementation is API-ready only. Production adapters and runtime wiring remain outside Stage 21.10.5c.
''')
        print("[9/10] [PASS] Machine report and Markdown implementation documentation written.")
        expected = {rel.as_posix() for rel in TARGETS}
        git(root, "add", "--", APP.as_posix(), TEST.as_posix(), TOOL.as_posix())
        git(root, "add", "-f", "--", SELF.as_posix(), REPORT.as_posix(), DOC.as_posix())
        staged = {line.strip().replace("\\", "/") for line in git(root, "diff", "--cached", "--name-only").stdout.splitlines() if line.strip()}
        if staged != expected:
            raise PatchError(f"staging_mismatch:{sorted(staged)}")
        commit_result = git(root, "commit", "-m", "Stage 21.10.5c: implement Premium Shop", check=False)
        if commit_result.returncode:
            raise PatchError(f"commit_failed:{commit_result.stdout}:{commit_result.stderr}")
        commit = git(root, "rev-parse", "HEAD").stdout.strip()
        changed = {line.strip().replace("\\", "/") for line in git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.splitlines() if line.strip()}
        if changed != expected:
            raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
        (root / FAILURE).unlink(missing_ok=True)
        print(f"[10/10] [PASS] Premium Shop implementation committed: {commit}")
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
