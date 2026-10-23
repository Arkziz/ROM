#!/usr/bin/env python3
"""ROM Stage 21.10.4c: implement the API-ready V2 Potion Trading service.

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

STAGE = "21.10.4c"
BRANCH = "rewrite/rom-v2"
PARENT = "8be088e5fc61a648cd685f210bb66b836411d129"
PREREQ = Path("reports/stage_21_10_4b_resolved_potion_trading_parity.json")
APP = Path("rom_v2/application/potion_trading.py")
TEST = Path("tests_v2/test_potion_trading.py")
TOOL = Path("tools/check_stage_21_10_4c_potion_trading.py")
REPORT = Path("reports/stage_21_10_4c_potion_trading_implementation.json")
DOC = Path("MD/STAGE_21_10_4C_POTION_TRADING_IMPLEMENTATION.md")
FAILURE = Path("reports/stage_21_10_4c_failure_rollback.json")
SELF = Path("patch/patch_21_10_4c_implement_potion_trading.py")
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
        raise PatchError("missing_stage_21_10_4b_prerequisite")
    contract = json.loads((root / PREREQ).read_text(encoding="utf-8"))
    expected = ("21.10.4b", "PASS", "GO_TO_IMPLEMENTATION")
    if (contract.get("stage"), contract.get("status"), contract.get("conclusion")) != expected:
        raise PatchError("invalid_stage_21_10_4b_prerequisite")
    summary = contract.get("summary", {})
    if summary.get("remaining_unresolved_contracts") != 0:
        raise PatchError("unresolved_potion_trading_contracts")
    if contract.get("implementation_authorized") is not True:
        raise PatchError("implementation_not_authorized")
    trading = contract.get("v2_potion_trading_contract", {})
    required = {
        "canonical_owner": "PotionTradingService", "typed_potion_keys": True,
        "positive_integer_quantity": True, "quoted_buy_price_locked": True,
        "quoted_sell_price_locked": True, "reservation_aware_sell": True,
        "deterministic_stack_plan": True, "stable_operation_key_required": True,
        "atomic_gold_inventory_receipt": True,
        "caller_owned_unit_of_work": True, "single_commit": True,
        "presentation_separate": True,
    }
    if any(trading.get(key) != value for key, value in required.items()):
        raise PatchError(f"invalid_potion_trading_contract:{trading}")
    if git(root, "diff", "--cached", "--name-only").stdout.strip():
        raise PatchError("index_not_clean")
    dirty = status_paths(root)
    if not dirty.issubset(ALLOWED_DIRTY):
        raise PatchError(f"unexpected_dirty:{sorted(dirty - ALLOWED_DIRTY)}")
    return contract


def backup(root):
    folder = root / "backup" / f"stage_21_10_4c_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
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
    return '''"""Pure API-ready Potion Trading service for ROM V2.

The service uses typed potion keys, immutable quoted prices, reservation-aware
sell validation, deterministic stack plans and one caller-owned transaction.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

class PotionTradingContractError(ValueError): pass
class PotionTradingConflictError(PotionTradingContractError): pass
class TradeDirection(str, Enum):
    BUY="buy"
    SELL="sell"

@dataclass(frozen=True, slots=True)
class PotionQuote:
    potion_key:str
    direction:TradeDirection
    unit_price:int

@dataclass(frozen=True, slots=True)
class PotionTradeCommand:
    operation_key:str
    user_id:int
    potion_key:str
    direction:TradeDirection
    quantity:int
    quoted_unit_price:int

@dataclass(frozen=True, slots=True)
class StackPlan:
    potion_key:str
    quantity_before:int
    quantity_delta:int
    quantity_after:int

@dataclass(frozen=True, slots=True)
class PotionTradeReceipt:
    operation_key:str
    user_id:int
    potion_key:str
    direction:TradeDirection
    quantity:int
    unit_price:int
    gold_delta:int
    balance_after:int
    quantity_after:int

@dataclass(frozen=True, slots=True)
class PotionTradeResult:
    receipt:PotionTradeReceipt
    replayed:bool

class PotionCatalogPort(Protocol):
    def get_unit_price(self,potion_key:str,direction:TradeDirection)->int|None: ...
class PotionInventoryPort(Protocol):
    def get_quantity(self,user_id:int,potion_key:str)->int: ...
    def get_reserved_quantity(self,user_id:int,potion_key:str)->int: ...
    def build_stack_plan(self,user_id:int,potion_key:str,delta:int)->StackPlan: ...
    def apply_stack_plan(self,user_id:int,plan:StackPlan)->None: ...
class PotionWalletPort(Protocol):
    def get_balance(self,user_id:int)->int: ...
    def debit(self,user_id:int,amount:int)->int: ...
    def credit(self,user_id:int,amount:int)->int: ...
class PotionReceiptPort(Protocol):
    def get_receipt(self,operation_key:str)->PotionTradeReceipt|None: ...
    def save_receipt(self,receipt:PotionTradeReceipt)->None: ...
class PotionTradingUnitOfWorkPort(Protocol):
    catalog:PotionCatalogPort
    inventory:PotionInventoryPort
    wallet:PotionWalletPort
    receipts:PotionReceiptPort
    def commit(self)->None: ...
    def rollback(self)->None: ...

class PotionTradingService:
    """Canonical V2 owner for atomic Alchemist potion buy and sell operations."""
    def execute(self,command:PotionTradeCommand,uow:PotionTradingUnitOfWorkPort)->PotionTradeResult:
        self._validate_command(command)
        try:
            existing=uow.receipts.get_receipt(command.operation_key)
            if existing is not None:
                if not self._same_payload(existing,command):
                    raise PotionTradingConflictError("operation_key_payload_conflict")
                return PotionTradeResult(existing,True)
            current_price=uow.catalog.get_unit_price(command.potion_key,command.direction)
            if current_price is None:raise PotionTradingContractError("potion_not_allowed")
            if current_price!=command.quoted_unit_price:raise PotionTradingContractError("stale_price")
            total=command.quantity*command.quoted_unit_price
            before=uow.inventory.get_quantity(command.user_id,command.potion_key)
            if before<0:raise PotionTradingContractError("invalid_inventory_quantity")
            if command.direction is TradeDirection.BUY:
                if uow.wallet.get_balance(command.user_id)<total:raise PotionTradingContractError("insufficient_gold")
                plan=uow.inventory.build_stack_plan(command.user_id,command.potion_key,command.quantity)
                self._validate_plan(plan,command,before)
                balance_after=uow.wallet.debit(command.user_id,total)
                gold_delta=-total
            else:
                reserved=uow.inventory.get_reserved_quantity(command.user_id,command.potion_key)
                if reserved<0 or reserved>before:raise PotionTradingContractError("invalid_reserved_quantity")
                if command.quantity>before-reserved:raise PotionTradingContractError("insufficient_available_quantity")
                plan=uow.inventory.build_stack_plan(command.user_id,command.potion_key,-command.quantity)
                self._validate_plan(plan,command,before)
                balance_after=uow.wallet.credit(command.user_id,total)
                gold_delta=total
            uow.inventory.apply_stack_plan(command.user_id,plan)
            receipt=PotionTradeReceipt(command.operation_key,command.user_id,command.potion_key,command.direction,command.quantity,command.quoted_unit_price,gold_delta,balance_after,plan.quantity_after)
            uow.receipts.save_receipt(receipt);uow.commit()
            return PotionTradeResult(receipt,False)
        except Exception:
            uow.rollback();raise
    @staticmethod
    def _validate_command(command:PotionTradeCommand)->None:
        if not command.operation_key.strip():raise PotionTradingContractError("operation_key_required")
        if command.user_id<=0:raise PotionTradingContractError("user_id_must_be_positive")
        if not command.potion_key.strip():raise PotionTradingContractError("potion_key_required")
        if not isinstance(command.direction,TradeDirection):raise PotionTradingContractError("invalid_direction")
        if not isinstance(command.quantity,int) or isinstance(command.quantity,bool):raise PotionTradingContractError("quantity_must_be_int")
        if command.quantity<=0:raise PotionTradingContractError("quantity_must_be_positive")
        if not isinstance(command.quoted_unit_price,int) or isinstance(command.quoted_unit_price,bool) or command.quoted_unit_price<=0:raise PotionTradingContractError("invalid_quoted_unit_price")
    @staticmethod
    def _validate_plan(plan:StackPlan,command:PotionTradeCommand,before:int)->None:
        expected_delta=command.quantity if command.direction is TradeDirection.BUY else -command.quantity
        if plan.potion_key!=command.potion_key or plan.quantity_before!=before or plan.quantity_delta!=expected_delta or plan.quantity_after!=before+expected_delta or plan.quantity_after<0:
            raise PotionTradingContractError("invalid_stack_plan")
    @staticmethod
    def _same_payload(receipt:PotionTradeReceipt,command:PotionTradeCommand)->bool:
        return receipt.user_id==command.user_id and receipt.potion_key==command.potion_key and receipt.direction is command.direction and receipt.quantity==command.quantity and receipt.unit_price==command.quoted_unit_price
'''


def test_text():
    return '''import unittest
from copy import deepcopy
from rom_v2.application.potion_trading import *
class Catalog:
 def __init__(self):self.prices={("small_hp",TradeDirection.BUY):5,("small_hp",TradeDirection.SELL):1}
 def get_unit_price(self,k,d):return self.prices.get((k,d))
class Inventory:
 def __init__(self,q=4,reserved=1):self.q=q;self.reserved=reserved;self.applied=[]
 def get_quantity(self,u,k):return self.q
 def get_reserved_quantity(self,u,k):return self.reserved
 def build_stack_plan(self,u,k,d):return StackPlan(k,self.q,d,self.q+d)
 def apply_stack_plan(self,u,p):self.q=p.quantity_after;self.applied.append(p)
class Wallet:
 def __init__(self,b=20):self.b=b
 def get_balance(self,u):return self.b
 def debit(self,u,a):
  if self.b<a:raise PotionTradingContractError("insufficient_gold")
  self.b-=a;return self.b
 def credit(self,u,a):self.b+=a;return self.b
class Receipts:
 def __init__(self):self.rows={}
 def get_receipt(self,k):return self.rows.get(k)
 def save_receipt(self,r):self.rows[r.operation_key]=r
class Uow:
 def __init__(self,b=20,q=4,reserved=1,fail=False):self.catalog=Catalog();self.inventory=Inventory(q,reserved);self.wallet=Wallet(b);self.receipts=Receipts();self.fail=fail;self.commits=0;self.rollbacks=0;self.snap=None
 def begin(self):self.snap=deepcopy((self.catalog,self.inventory,self.wallet,self.receipts))
 def commit(self):
  if self.fail:raise RuntimeError("commit_failure")
  self.commits+=1;self.snap=None
 def rollback(self):
  self.rollbacks+=1
  if self.snap:self.catalog,self.inventory,self.wallet,self.receipts=self.snap;self.snap=None
def cmd(k="op",d=TradeDirection.BUY,q=2,p=5):return PotionTradeCommand(k,1,"small_hp",d,q,p)
def execute(u,c):u.begin();return PotionTradingService().execute(c,u)
class Tests(unittest.TestCase):
 def test_buy(self):
  u=Uow();r=execute(u,cmd());self.assertEqual(r.receipt.gold_delta,-10);self.assertEqual(u.wallet.b,10);self.assertEqual(u.inventory.q,6);self.assertEqual(u.commits,1)
 def test_sell_reservation_aware(self):
  u=Uow();r=execute(u,cmd(d=TradeDirection.SELL,q=3,p=1));self.assertEqual(r.receipt.gold_delta,3);self.assertEqual(u.inventory.q,1)
 def test_reserved_quantity_blocks_sell(self):
  u=Uow()
  with self.assertRaisesRegex(PotionTradingContractError,"insufficient_available_quantity"):execute(u,cmd(d=TradeDirection.SELL,q=4,p=1))
  self.assertEqual(u.inventory.q,4);self.assertEqual(u.wallet.b,20)
 def test_stale_price_fails_closed(self):
  u=Uow()
  with self.assertRaisesRegex(PotionTradingContractError,"stale_price"):execute(u,cmd(p=6))
  self.assertFalse(u.inventory.applied);self.assertEqual(u.wallet.b,20)
 def test_insufficient_gold_fails_closed(self):
  u=Uow(b=9)
  with self.assertRaisesRegex(PotionTradingContractError,"insufficient_gold"):execute(u,cmd())
  self.assertFalse(u.inventory.applied)
 def test_replay_and_conflict(self):
  u=Uow();first=execute(u,cmd());u.begin();again=PotionTradingService().execute(cmd(),u);self.assertTrue(again.replayed);self.assertEqual(first.receipt,again.receipt);u.begin()
  with self.assertRaises(PotionTradingConflictError):PotionTradingService().execute(cmd(q=1),u)
 def test_commit_failure_rolls_back_all(self):
  u=Uow(fail=True)
  with self.assertRaisesRegex(RuntimeError,"commit_failure"):execute(u,cmd())
  self.assertEqual(u.wallet.b,20);self.assertEqual(u.inventory.q,4);self.assertFalse(u.receipts.rows)
 def test_invalid_quantity(self):
  for q in (0,-1,True,1.5):
   with self.subTest(q=q),self.assertRaises(PotionTradingContractError):PotionTradingService().execute(cmd(q=q),Uow())
 def test_restart_replay(self):
  first=Uow();original=execute(first,cmd());second=deepcopy(first);second.begin();replay=PotionTradingService().execute(cmd(),second);self.assertTrue(replay.replayed);self.assertEqual(replay.receipt,original.receipt)
if __name__=="__main__":unittest.main()
'''


def tool_text():
    return '''#!/usr/bin/env python3
"""Targeted Stage 21.10.4c Potion Trading verifier."""
import ast
from pathlib import Path

root=Path(__file__).resolve().parents[1]
app=root/"rom_v2/application/potion_trading.py"
test=root/"tests_v2/test_potion_trading.py"
for path in (app,test): ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
source=app.read_text(encoding="utf-8")
required=("class PotionTradingService","class PotionTradeCommand","class PotionTradeReceipt","operation_key_payload_conflict","stale_price","insufficient_available_quantity")
missing=[token for token in required if token not in source]
if missing: raise SystemExit(f"missing_contract_tokens:{missing}")
for forbidden in ("sqlite3","aiogram","telegram"):
    if forbidden in source.lower(): raise SystemExit(f"forbidden_dependency:{forbidden}")
print("STAGE_21_10_4C_POTION_TRADING_SMOKE: PASS")
'''


def run_ci(root, env):
    temporary = root / "reports/.stage_21_10_4c_ci.tmp.json"
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
        print("[1/10] [PASS] Stage 21.10.4b zero-unresolved implementation prerequisite verified.")
        print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
        before = protected(root)
        folder, state = backup(root)
        print("[3/10] [PASS] All mutation targets backed up before production mutation.")
        write(root, APP, app_text())
        write(root, TEST, test_text())
        write(root, TOOL, tool_text())
        print("[4/10] [PASS] PotionTradingService, immutable command/quote/stack-plan/receipt DTOs and ports implemented.")
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
        print("[6/10] [PASS] Buy/sell quantity, accepted prices, reservations, stack plans, idempotency, rollback and restart tests passed.")
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
            "application_service": "PotionTradingService",
            "implementation": APP.as_posix(),
            "tests": TEST.as_posix(),
            "implemented": [
                "typed_potion_keys", "positive_integer_quantity",
                "quoted_buy_price_locked", "quoted_sell_price_locked",
                "reservation_aware_sell", "deterministic_stack_plan",
                "stable_operation_key", "same_payload_idempotent_replay",
                "changed_payload_conflict", "stale_price_rejection",
                "atomic_gold_inventory_receipt", "single_commit", "atomic_rollback",
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
        write(root, DOC, '''# Stage 21.10.4c - Potion Trading implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Canonical owner: `PotionTradingService`
- Typed potion keys with accepted buy/sell prices
- Non-negative balance: **enforced**
- Stable operation key and deterministic stack plan: **implemented**
- Reservation-aware atomic trade with idempotent replay: **idempotent**
- Changed-payload replay: **conflict**
- Single caller-owned commit and atomic rollback: **implemented**
- SQLite / production persistence: **NOT_CONNECTED**
- Runtime / Telegram: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

The implementation is API-ready only. Production adapters and runtime wiring remain outside Stage 21.10.4c.
''')
        print("[9/10] [PASS] Machine report and Markdown implementation documentation written.")
        expected = {rel.as_posix() for rel in TARGETS}
        git(root, "add", "--", APP.as_posix(), TEST.as_posix(), TOOL.as_posix())
        git(root, "add", "-f", "--", SELF.as_posix(), REPORT.as_posix(), DOC.as_posix())
        staged = {line.strip().replace("\\", "/") for line in git(root, "diff", "--cached", "--name-only").stdout.splitlines() if line.strip()}
        if staged != expected:
            raise PatchError(f"staging_mismatch:{sorted(staged)}")
        commit_result = git(root, "commit", "-m", "Stage 21.10.4c: implement Potion Trading", check=False)
        if commit_result.returncode:
            raise PatchError(f"commit_failed:{commit_result.stdout}:{commit_result.stderr}")
        commit = git(root, "rev-parse", "HEAD").stdout.strip()
        changed = {line.strip().replace("\\", "/") for line in git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.splitlines() if line.strip()}
        if changed != expected:
            raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
        (root / FAILURE).unlink(missing_ok=True)
        print(f"[10/10] [PASS] Potion Trading implementation committed: {commit}")
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
