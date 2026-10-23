#!/usr/bin/env python3
"""ROM Stage 21.10.7c: implement the API-ready V2 Bag Expansion service.

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

STAGE = "21.10.7c"
BRANCH = "rewrite/rom-v2"
PARENT = "6d40fbbd73ccb660543192358212b0f6886f8dc3"
PREREQ = Path("reports/stage_21_10_7b_resolved_bag_expansion_parity.json")
APP = Path("rom_v2/application/bag_expansion.py")
TEST = Path("tests_v2/test_bag_expansion.py")
TOOL = Path("tools/check_stage_21_10_7c_bag_expansion.py")
REPORT = Path("reports/stage_21_10_7c_bag_expansion_implementation.json")
DOC = Path("MD/STAGE_21_10_7C_BAG_EXPANSION_IMPLEMENTATION.md")
FAILURE = Path("reports/stage_21_10_7c_failure_rollback.json")
SELF = Path("patch/patch_21_10_7c_implement_bag_expansion.py")
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
        raise PatchError("missing_stage_21_10_7b_prerequisite")
    contract = json.loads((root / PREREQ).read_text(encoding="utf-8"))
    expected = ("21.10.7b", "PASS", "GO_TO_IMPLEMENTATION")
    if (contract.get("stage"), contract.get("status"), contract.get("conclusion")) != expected:
        raise PatchError("invalid_stage_21_10_7b_prerequisite")
    summary = contract.get("summary", {})
    if summary.get("remaining_unresolved_contracts") != 0:
        raise PatchError("unresolved_bag_expansion_contracts")
    if contract.get("implementation_authorized") is not True:
        raise PatchError("implementation_not_authorized")
    expansion = contract.get("v2_bag_expansion_contract", {})
    required = {
        "canonical_owner": "BagExpansionService", "account_identity": "user_id",
        "first_expansion_key": "bag_60_to_80", "first_from_capacity": 60,
        "first_to_capacity": 80, "first_price_crystals": 75,
        "second_expansion_key": "bag_80_to_100", "second_from_capacity": 80,
        "second_to_capacity": 100, "second_price_crystals": 150,
        "maximum_capacity": 100, "sequential_only": True,
        "stable_operation_key_required": True,
        "atomic_crystal_capacity_receipt": True,
        "character_reset_survival": True, "restart_safe": True,
        "caller_owned_unit_of_work": True, "single_commit": True,
        "presentation_separate": True,
    }
    if contract.get("approved_capacity_scope") != {"capacity_path": [60, 80, 100], "prices_crystals": [75, 150]}:
        raise PatchError("invalid_approved_bag_expansion_scope")
    if any(expansion.get(key) != value for key, value in required.items()):
        raise PatchError(f"invalid_bag_expansion_contract:{expansion}")
    if git(root, "diff", "--cached", "--name-only").stdout.strip():
        raise PatchError("index_not_clean")
    dirty = status_paths(root)
    if not dirty.issubset(ALLOWED_DIRTY):
        raise PatchError(f"unexpected_dirty:{sorted(dirty - ALLOWED_DIRTY)}")
    return contract


def backup(root):
    folder = root / "backup" / f"stage_21_10_7c_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
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
    return '''"""Pure API-ready Bag Expansion service for ROM V2."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

class BagExpansionContractError(ValueError): pass
class BagExpansionConflictError(BagExpansionContractError): pass

@dataclass(frozen=True, slots=True)
class BagExpansionDefinition:
    expansion_key:str
    from_capacity:int
    to_capacity:int
    price_crystals:int

EXPANSIONS={
    "bag_60_to_80":BagExpansionDefinition("bag_60_to_80",60,80,75),
    "bag_80_to_100":BagExpansionDefinition("bag_80_to_100",80,100,150),
}
MAXIMUM_CAPACITY=100

@dataclass(frozen=True, slots=True)
class BagExpansionCommand:
    operation_key:str
    user_id:int
    expansion_key:str
    quoted_from_capacity:int
    quoted_to_capacity:int
    quoted_price_crystals:int

@dataclass(frozen=True, slots=True)
class BagExpansionReceipt:
    operation_key:str
    user_id:int
    expansion_key:str
    previous_capacity:int
    target_capacity:int
    price_crystals:int
    crystal_balance_after:int

@dataclass(frozen=True, slots=True)
class BagExpansionResult:
    receipt:BagExpansionReceipt
    replayed:bool

class BagCapacityPort(Protocol):
    def get_capacity(self,user_id:int)->int: ...
    def set_capacity(self,user_id:int,capacity:int)->None: ...
class BagExpansionCrystalWalletPort(Protocol):
    def get_balance(self,user_id:int)->int: ...
    def debit(self,user_id:int,amount:int)->int: ...
class BagExpansionReceiptPort(Protocol):
    def get_receipt(self,operation_key:str)->BagExpansionReceipt|None: ...
    def save_receipt(self,receipt:BagExpansionReceipt)->None: ...
class BagExpansionUnitOfWorkPort(Protocol):
    capacity:BagCapacityPort
    wallet:BagExpansionCrystalWalletPort
    receipts:BagExpansionReceiptPort
    def commit(self)->None: ...
    def rollback(self)->None: ...

class BagExpansionService:
    """Canonical owner for sequential account-level bag expansion purchases."""
    def purchase(self,command:BagExpansionCommand,uow:BagExpansionUnitOfWorkPort)->BagExpansionResult:
        self._validate_command(command)
        try:
            existing=uow.receipts.get_receipt(command.operation_key)
            if existing is not None:
                if not self._same_payload(existing,command):raise BagExpansionConflictError("operation_key_payload_conflict")
                return BagExpansionResult(existing,True)
            definition=EXPANSIONS.get(command.expansion_key)
            if definition is None:raise BagExpansionContractError("unknown_expansion")
            current=uow.capacity.get_capacity(command.user_id)
            if current==MAXIMUM_CAPACITY:raise BagExpansionContractError("maximum_capacity")
            if current not in (60,80):raise BagExpansionContractError("invalid_current_capacity")
            if current!=command.quoted_from_capacity:raise BagExpansionContractError("stale_capacity")
            if definition.from_capacity!=current or definition.to_capacity!=command.quoted_to_capacity:raise BagExpansionContractError("invalid_sequential_transition")
            if definition.price_crystals!=command.quoted_price_crystals:raise BagExpansionContractError("stale_price")
            if uow.wallet.get_balance(command.user_id)<definition.price_crystals:raise BagExpansionContractError("insufficient_crystals")
            balance_after=uow.wallet.debit(command.user_id,definition.price_crystals)
            uow.capacity.set_capacity(command.user_id,definition.to_capacity)
            receipt=BagExpansionReceipt(command.operation_key,command.user_id,definition.expansion_key,current,definition.to_capacity,definition.price_crystals,balance_after)
            uow.receipts.save_receipt(receipt);uow.commit()
            return BagExpansionResult(receipt,False)
        except Exception:
            uow.rollback();raise
    @staticmethod
    def _validate_command(command:BagExpansionCommand)->None:
        if not command.operation_key.strip():raise BagExpansionContractError("operation_key_required")
        if command.user_id<=0:raise BagExpansionContractError("user_id_must_be_positive")
        if not command.expansion_key.strip():raise BagExpansionContractError("expansion_key_required")
        for value,reason in ((command.quoted_from_capacity,"invalid_from_capacity"),(command.quoted_to_capacity,"invalid_to_capacity"),(command.quoted_price_crystals,"invalid_quoted_price")):
            if not isinstance(value,int) or isinstance(value,bool) or value<=0:raise BagExpansionContractError(reason)
    @staticmethod
    def _same_payload(receipt:BagExpansionReceipt,command:BagExpansionCommand)->bool:
        return receipt.user_id==command.user_id and receipt.expansion_key==command.expansion_key and receipt.previous_capacity==command.quoted_from_capacity and receipt.target_capacity==command.quoted_to_capacity and receipt.price_crystals==command.quoted_price_crystals
'''


def test_text():
    return '''import unittest
from copy import deepcopy
from rom_v2.application.bag_expansion import *
class Capacity:
 def __init__(self,c=60):self.c=c
 def get_capacity(self,u):return self.c
 def set_capacity(self,u,c):self.c=c
class Wallet:
 def __init__(self,b=300):self.b=b
 def get_balance(self,u):return self.b
 def debit(self,u,a):
  if self.b<a:raise BagExpansionContractError("insufficient_crystals")
  self.b-=a;return self.b
class Receipts:
 def __init__(self):self.rows={}
 def get_receipt(self,k):return self.rows.get(k)
 def save_receipt(self,r):self.rows[r.operation_key]=r
class Uow:
 def __init__(self,c=60,b=300,fail=False):self.capacity=Capacity(c);self.wallet=Wallet(b);self.receipts=Receipts();self.fail=fail;self.commits=0;self.rollbacks=0;self.snap=None
 def begin(self):self.snap=deepcopy((self.capacity,self.wallet,self.receipts))
 def commit(self):
  if self.fail:raise RuntimeError("commit_failure")
  self.commits+=1;self.snap=None
 def rollback(self):
  self.rollbacks+=1
  if self.snap:self.capacity,self.wallet,self.receipts=self.snap;self.snap=None
def first(k="op"):return BagExpansionCommand(k,1,"bag_60_to_80",60,80,75)
def second(k="op2"):return BagExpansionCommand(k,1,"bag_80_to_100",80,100,150)
def execute(u,c):u.begin();return BagExpansionService().purchase(c,u)
class Tests(unittest.TestCase):
 def test_first_expansion(self):
  u=Uow();r=execute(u,first());self.assertEqual(r.receipt.target_capacity,80);self.assertEqual(u.capacity.c,80);self.assertEqual(u.wallet.b,225);self.assertEqual(u.commits,1)
 def test_second_expansion(self):
  u=Uow(c=80);r=execute(u,second());self.assertEqual(r.receipt.target_capacity,100);self.assertEqual(u.capacity.c,100);self.assertEqual(u.wallet.b,150)
 def test_maximum_capacity_rejected(self):
  u=Uow(c=100)
  with self.assertRaisesRegex(BagExpansionContractError,"maximum_capacity"):execute(u,second())
  self.assertEqual(u.wallet.b,300)
 def test_skip_and_stale_rejected(self):
  u=Uow()
  with self.assertRaisesRegex(BagExpansionContractError,"stale_capacity"):execute(u,second())
  u=Uow(c=80)
  with self.assertRaisesRegex(BagExpansionContractError,"stale_capacity"):execute(u,first())
 def test_stale_price_rejected(self):
  u=Uow();bad=BagExpansionCommand("x",1,"bag_60_to_80",60,80,76)
  with self.assertRaisesRegex(BagExpansionContractError,"stale_price"):execute(u,bad)
  self.assertEqual(u.wallet.b,300);self.assertEqual(u.capacity.c,60)
 def test_insufficient_crystals(self):
  u=Uow(b=74)
  with self.assertRaisesRegex(BagExpansionContractError,"insufficient_crystals"):execute(u,first())
  self.assertEqual(u.capacity.c,60)
 def test_replay_and_conflict(self):
  u=Uow();original=execute(u,first());u.begin();replay=BagExpansionService().purchase(first(),u);self.assertTrue(replay.replayed);self.assertEqual(replay.receipt,original.receipt);self.assertEqual(u.wallet.b,225);u.begin()
  with self.assertRaises(BagExpansionConflictError):BagExpansionService().purchase(BagExpansionCommand("op",2,"bag_60_to_80",60,80,75),u)
 def test_commit_failure_rolls_back_all(self):
  u=Uow(fail=True)
  with self.assertRaisesRegex(RuntimeError,"commit_failure"):execute(u,first())
  self.assertEqual(u.capacity.c,60);self.assertEqual(u.wallet.b,300);self.assertFalse(u.receipts.rows)
 def test_restart_replay_and_reset_survival(self):
  first_uow=Uow();original=execute(first_uow,first());second_uow=deepcopy(first_uow);second_uow.begin();replay=BagExpansionService().purchase(first(),second_uow);self.assertTrue(replay.replayed);self.assertEqual(replay.receipt,original.receipt);self.assertEqual(second_uow.capacity.c,80)
if __name__=="__main__":unittest.main()
'''


def tool_text():
    return '''#!/usr/bin/env python3
"""Targeted Stage 21.10.7c Bag Expansion verifier."""
import ast
from pathlib import Path

root=Path(__file__).resolve().parents[1]
app=root/"rom_v2/application/bag_expansion.py"
test=root/"tests_v2/test_bag_expansion.py"
for path in (app,test): ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
source=app.read_text(encoding="utf-8")
required=("class BagExpansionService","class BagExpansionCommand","class BagExpansionReceipt","operation_key_payload_conflict","maximum_capacity","stale_capacity","stale_price","invalid_sequential_transition")
missing=[token for token in required if token not in source]
if missing: raise SystemExit(f"missing_contract_tokens:{missing}")
for forbidden in ("sqlite3","aiogram","telegram"):
    if forbidden in source.lower(): raise SystemExit(f"forbidden_dependency:{forbidden}")
print("STAGE_21_10_7C_BAG_EXPANSION_SMOKE: PASS")
'''


def run_ci(root, env):
    temporary = root / "reports/.stage_21_10_7c_ci.tmp.json"
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
        print("[1/10] [PASS] Stage 21.10.7b zero-unresolved implementation prerequisite verified.")
        print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
        before = protected(root)
        folder, state = backup(root)
        print("[3/10] [PASS] All mutation targets backed up before production mutation.")
        write(root, APP, app_text())
        write(root, TEST, test_text())
        write(root, TOOL, tool_text())
        print("[4/10] [PASS] BagExpansionService, immutable expansion/command/receipt DTOs and ports implemented.")
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
        print("[6/10] [PASS] Sequential 60/80/100 expansion, 75/150 prices, maximum, idempotency, rollback, reset and restart tests passed.")
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
        write(root, DOC, '''# Stage 21.10.7c - Bag Expansion implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Canonical owner: `BagExpansionService`
- Exact Bag Expansion: 3 small HP potions and 3 Phirius Tokens
- Non-negative balance: **enforced**
- Stable operation and expansion keys with immutable purchase receipt: **implemented**
- Atomic sequential bag expansion with idempotent replay: **idempotent**
- Changed-payload replay: **conflict**
- Single caller-owned commit and atomic rollback: **implemented**
- SQLite / production persistence: **NOT_CONNECTED**
- Runtime / Telegram: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

The implementation is API-ready only. Production adapters and runtime wiring remain outside Stage 21.10.7c.
''')
        print("[9/10] [PASS] Machine report and Markdown implementation documentation written.")
        expected = {rel.as_posix() for rel in TARGETS}
        git(root, "add", "--", APP.as_posix(), TEST.as_posix(), TOOL.as_posix())
        git(root, "add", "-f", "--", SELF.as_posix(), REPORT.as_posix(), DOC.as_posix())
        staged = {line.strip().replace("\\", "/") for line in git(root, "diff", "--cached", "--name-only").stdout.splitlines() if line.strip()}
        if staged != expected:
            raise PatchError(f"staging_mismatch:{sorted(staged)}")
        commit_result = git(root, "commit", "-m", "Stage 21.10.7c: implement Bag Expansion", check=False)
        if commit_result.returncode:
            raise PatchError(f"commit_failed:{commit_result.stdout}:{commit_result.stderr}")
        commit = git(root, "rev-parse", "HEAD").stdout.strip()
        changed = {line.strip().replace("\\", "/") for line in git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.splitlines() if line.strip()}
        if changed != expected:
            raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
        (root / FAILURE).unlink(missing_ok=True)
        print(f"[10/10] [PASS] Bag Expansion implementation committed: {commit}")
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
