#!/usr/bin/env python3
"""ROM Stage 21.10.2c: implement the API-ready V2 Crystal Wallet/Ledger service.

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

STAGE = "21.10.2c"
BRANCH = "rewrite/rom-v2"
PARENT = "1181e773d1818586f1724be9f788f48726abfcd0"
PREREQ = Path("reports/stage_21_10_2b_resolved_crystal_wallet_ledger_parity.json")
APP = Path("rom_v2/application/crystal_wallet_ledger.py")
TEST = Path("tests_v2/test_crystal_wallet_ledger.py")
TOOL = Path("tools/check_stage_21_10_2c_crystal_wallet_ledger.py")
REPORT = Path("reports/stage_21_10_2c_crystal_wallet_ledger_implementation.json")
DOC = Path("MD/STAGE_21_10_1C_CRYSTAL_WALLET_LEDGER_IMPLEMENTATION.md")
FAILURE = Path("reports/stage_21_10_2c_failure_rollback.json")
SELF = Path("patch/patch_21_10_2c_implement_crystal_wallet_ledger.py")
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
        raise PatchError("missing_stage_21_10_2b_prerequisite")
    contract = json.loads((root / PREREQ).read_text(encoding="utf-8"))
    expected = ("21.10.2b", "PASS", "GO_TO_IMPLEMENTATION")
    if (contract.get("stage"), contract.get("status"), contract.get("conclusion")) != expected:
        raise PatchError("invalid_stage_21_10_2b_prerequisite")
    summary = contract.get("summary", {})
    if summary.get("remaining_unresolved_contracts") != 0:
        raise PatchError("unresolved_crystal_wallet_ledger_contracts")
    if contract.get("implementation_authorized") is not True:
        raise PatchError("implementation_not_authorized")
    wallet = contract.get("v2_crystal_wallet_ledger_contract", {})
    required = {
        "canonical_owner": "CrystalWalletLedgerService",
        "identity": "user_id",
        "amount_type": "int",
        "non_negative_balance": True,
        "append_only_ledger": True,
        "stable_idempotency_key_required": True,
        "exact_once_compensation": True,
        "caller_owned_unit_of_work": True,
        "single_commit": True,
        "presentation_separate": True,
    }
    if any(wallet.get(key) != value for key, value in required.items()):
        raise PatchError(f"invalid_crystal_wallet_ledger_contract:{wallet}")
    if git(root, "diff", "--cached", "--name-only").stdout.strip():
        raise PatchError("index_not_clean")
    dirty = status_paths(root)
    if not dirty.issubset(ALLOWED_DIRTY):
        raise PatchError(f"unexpected_dirty:{sorted(dirty - ALLOWED_DIRTY)}")
    return contract


def backup(root):
    folder = root / "backup" / f"stage_21_10_2c_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
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
    return '''"""Pure API-ready Crystal Wallet/Ledger service for ROM V2."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

class CrystalWalletContractError(ValueError): pass
class CrystalWalletConflictError(CrystalWalletContractError): pass
class CrystalDirection(str, Enum):
    CREDIT="credit"
    DEBIT="debit"

@dataclass(frozen=True, slots=True)
class CrystalWalletCommand:
    idempotency_key: str
    user_id: int
    direction: CrystalDirection
    amount: int
    reason_code: str
    source: str

@dataclass(frozen=True, slots=True)
class CrystalLedgerTransaction:
    transaction_id: str
    idempotency_key: str
    user_id: int
    direction: CrystalDirection
    amount: int
    balance_before: int
    balance_after: int
    reason_code: str
    source: str
    original_transaction_id: str | None
    created_at: datetime

@dataclass(frozen=True, slots=True)
class CrystalWalletResult:
    transaction: CrystalLedgerTransaction
    replayed: bool

class CrystalWalletRepositoryPort(Protocol):
    def get_balance(self,user_id:int)->int: ...
    def set_balance(self,user_id:int,balance:int)->None: ...
    def get_by_idempotency_key(self,key:str)->CrystalLedgerTransaction|None: ...
    def get_transaction(self,transaction_id:str)->CrystalLedgerTransaction|None: ...
    def get_compensation(self,original_transaction_id:str)->CrystalLedgerTransaction|None: ...
    def append_transaction(self,transaction:CrystalLedgerTransaction)->None: ...

class CrystalWalletUnitOfWorkPort(Protocol):
    wallet: CrystalWalletRepositoryPort
    def next_transaction_id(self)->str: ...
    def now(self)->datetime: ...
    def commit(self)->None: ...
    def rollback(self)->None: ...

class CrystalWalletLedgerService:
    """Canonical owner for integer crystal mutation and append-only history."""
    def execute(self,command:CrystalWalletCommand,uow:CrystalWalletUnitOfWorkPort)->CrystalWalletResult:
        self._validate(command)
        try:
            existing=uow.wallet.get_by_idempotency_key(command.idempotency_key)
            if existing is not None:
                if not self._same(existing,command): raise CrystalWalletConflictError("idempotency_key_payload_conflict")
                return CrystalWalletResult(existing,True)
            before=uow.wallet.get_balance(command.user_id)
            if not isinstance(before,int) or isinstance(before,bool) or before<0: raise CrystalWalletContractError("invalid_stored_balance")
            after=before+command.amount if command.direction is CrystalDirection.CREDIT else before-command.amount
            if after<0: raise CrystalWalletContractError("insufficient_crystals")
            transaction=CrystalLedgerTransaction(uow.next_transaction_id(),command.idempotency_key,command.user_id,command.direction,command.amount,before,after,command.reason_code,command.source,None,uow.now())
            uow.wallet.set_balance(command.user_id,after)
            uow.wallet.append_transaction(transaction)
            uow.commit()
            return CrystalWalletResult(transaction,False)
        except Exception:
            uow.rollback(); raise

    def compensate(self,*,original_transaction_id:str,idempotency_key:str,reason_code:str,source:str,uow:CrystalWalletUnitOfWorkPort)->CrystalWalletResult:
        if not original_transaction_id.strip(): raise CrystalWalletContractError("original_transaction_id_required")
        if not idempotency_key.strip(): raise CrystalWalletContractError("idempotency_key_required")
        try:
            existing=uow.wallet.get_by_idempotency_key(idempotency_key)
            if existing is not None:
                if existing.original_transaction_id!=original_transaction_id or existing.reason_code!=reason_code or existing.source!=source: raise CrystalWalletConflictError("idempotency_key_payload_conflict")
                return CrystalWalletResult(existing,True)
            original=uow.wallet.get_transaction(original_transaction_id)
            if original is None: raise CrystalWalletContractError("original_transaction_not_found")
            if original.original_transaction_id is not None: raise CrystalWalletContractError("compensation_of_compensation_forbidden")
            if uow.wallet.get_compensation(original_transaction_id) is not None: raise CrystalWalletConflictError("original_already_compensated")
            direction=CrystalDirection.DEBIT if original.direction is CrystalDirection.CREDIT else CrystalDirection.CREDIT
            command=CrystalWalletCommand(idempotency_key,original.user_id,direction,original.amount,reason_code,source)
            self._validate(command)
            before=uow.wallet.get_balance(original.user_id)
            after=before+original.amount if direction is CrystalDirection.CREDIT else before-original.amount
            if after<0: raise CrystalWalletContractError("insufficient_crystals")
            transaction=CrystalLedgerTransaction(uow.next_transaction_id(),idempotency_key,original.user_id,direction,original.amount,before,after,reason_code,source,original_transaction_id,uow.now())
            uow.wallet.set_balance(original.user_id,after); uow.wallet.append_transaction(transaction); uow.commit()
            return CrystalWalletResult(transaction,False)
        except Exception:
            uow.rollback(); raise

    @staticmethod
    def _validate(command:CrystalWalletCommand)->None:
        if not command.idempotency_key.strip(): raise CrystalWalletContractError("idempotency_key_required")
        if command.user_id<=0: raise CrystalWalletContractError("user_id_must_be_positive")
        if not isinstance(command.amount,int) or isinstance(command.amount,bool): raise CrystalWalletContractError("amount_must_be_int")
        if command.amount<=0: raise CrystalWalletContractError("amount_must_be_positive")
        if not isinstance(command.direction,CrystalDirection): raise CrystalWalletContractError("invalid_direction")
        if not command.reason_code.strip(): raise CrystalWalletContractError("reason_code_required")
        if not command.source.strip(): raise CrystalWalletContractError("source_required")
    @staticmethod
    def _same(transaction,command):
        return transaction.user_id==command.user_id and transaction.direction is command.direction and transaction.amount==command.amount and transaction.reason_code==command.reason_code and transaction.source==command.source and transaction.original_transaction_id is None
'''


def test_text():
    return '''import unittest
from copy import deepcopy
from datetime import datetime, timezone
from rom_v2.application.crystal_wallet_ledger import *
class Repo:
 def __init__(self,balance=0): self.b={1:balance};self.by_key={};self.by_id={}
 def get_balance(self,u):return self.b.get(u,0)
 def set_balance(self,u,b):self.b[u]=b
 def get_by_idempotency_key(self,k):return self.by_key.get(k)
 def get_transaction(self,t):return self.by_id.get(t)
 def get_compensation(self,o):return next((x for x in self.by_id.values() if x.original_transaction_id==o),None)
 def append_transaction(self,t):
  if t.idempotency_key in self.by_key:raise RuntimeError("duplicate_key")
  self.by_key[t.idempotency_key]=t;self.by_id[t.transaction_id]=t
class Uow:
 def __init__(self,b=0,fail=False):self.wallet=Repo(b);self.fail=fail;self.n=0;self.commits=0;self.rollbacks=0;self.snap=None
 def begin(self):self.snap=deepcopy((self.wallet.b,self.wallet.by_key,self.wallet.by_id))
 def next_transaction_id(self):self.n+=1;return f"tx-{self.n}"
 def now(self):return datetime(2026,1,1,tzinfo=timezone.utc)
 def commit(self):
  if self.fail:raise RuntimeError("commit_failure")
  self.commits+=1;self.snap=None
 def rollback(self):
  self.rollbacks+=1
  if self.snap:self.wallet.b,self.wallet.by_key,self.wallet.by_id=self.snap;self.snap=None
def cmd(k="k1",d=CrystalDirection.CREDIT,a=5):return CrystalWalletCommand(k,1,d,a,"test","unit")
class Tests(unittest.TestCase):
 def run_cmd(self,u,c):u.begin();return CrystalWalletLedgerService().execute(c,u)
 def test_credit_and_debit(self):
  u=Uow(2);self.assertEqual(self.run_cmd(u,cmd()).transaction.balance_after,7);self.assertEqual(self.run_cmd(u,cmd("k2",CrystalDirection.DEBIT,3)).transaction.balance_after,4)
 def test_insufficient_fails_closed(self):
  u=Uow(1)
  with self.assertRaisesRegex(CrystalWalletContractError,"insufficient_crystals"):self.run_cmd(u,cmd(d=CrystalDirection.DEBIT,a=2))
  self.assertEqual(u.wallet.get_balance(1),1);self.assertFalse(u.wallet.by_id)
 def test_same_replay_and_changed_conflict(self):
  u=Uow();first=self.run_cmd(u,cmd());u.begin();self.assertTrue(CrystalWalletLedgerService().execute(cmd(),u).replayed);u.begin()
  with self.assertRaises(CrystalWalletConflictError):CrystalWalletLedgerService().execute(cmd(a=6),u)
  self.assertEqual(u.wallet.get_balance(1),5);self.assertEqual(first.transaction.transaction_id,"tx-1")
 def test_compensation_exact_once(self):
  u=Uow();original=self.run_cmd(u,cmd()).transaction;u.begin();service=CrystalWalletLedgerService();comp=service.compensate(original_transaction_id=original.transaction_id,idempotency_key="c1",reason_code="reverse",source="unit",uow=u)
  self.assertEqual(comp.transaction.balance_after,0);u.begin();self.assertTrue(service.compensate(original_transaction_id=original.transaction_id,idempotency_key="c1",reason_code="reverse",source="unit",uow=u).replayed);u.begin()
  with self.assertRaises(CrystalWalletConflictError):service.compensate(original_transaction_id=original.transaction_id,idempotency_key="c2",reason_code="reverse",source="unit",uow=u)
 def test_compensation_of_compensation_forbidden(self):
  u=Uow();o=self.run_cmd(u,cmd()).transaction;u.begin();c=CrystalWalletLedgerService().compensate(original_transaction_id=o.transaction_id,idempotency_key="c1",reason_code="r",source="u",uow=u).transaction;u.begin()
  with self.assertRaisesRegex(CrystalWalletContractError,"compensation_of_compensation_forbidden"):CrystalWalletLedgerService().compensate(original_transaction_id=c.transaction_id,idempotency_key="c2",reason_code="r",source="u",uow=u)
 def test_commit_failure_rolls_back(self):
  u=Uow(fail=True)
  with self.assertRaisesRegex(RuntimeError,"commit_failure"):self.run_cmd(u,cmd())
  self.assertEqual(u.wallet.get_balance(1),0);self.assertFalse(u.wallet.by_id)
 def test_int_and_positive_validation(self):
  for value in (1.0,True):
   with self.assertRaisesRegex(CrystalWalletContractError,"amount_must_be_int"):CrystalWalletLedgerService().execute(cmd(a=value),Uow())
  with self.assertRaisesRegex(CrystalWalletContractError,"amount_must_be_positive"):CrystalWalletLedgerService().execute(cmd(a=0),Uow())
 def test_immutable_transaction(self):
  t=self.run_cmd(Uow(),cmd()).transaction
  with self.assertRaises(Exception):t.amount=99
 def test_restart_replay(self):
  first=Uow();original=self.run_cmd(first,cmd());second=Uow();second.wallet=deepcopy(first.wallet);second.begin();replay=CrystalWalletLedgerService().execute(cmd(),second);self.assertTrue(replay.replayed);self.assertEqual(replay.transaction,original.transaction)
if __name__=="__main__":unittest.main()
'''


def tool_text():
    return '''#!/usr/bin/env python3
"""Targeted Stage 21.10.2c Crystal Wallet/Ledger verifier."""
import ast
from pathlib import Path

root=Path(__file__).resolve().parents[1]
app=root/"rom_v2/application/crystal_wallet_ledger.py"
test=root/"tests_v2/test_crystal_wallet_ledger.py"
for path in (app,test): ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
source=app.read_text(encoding="utf-8")
required=("class CrystalWalletLedgerService","class CrystalLedgerTransaction","class CrystalWalletCommand","idempotency_key_payload_conflict","original_already_compensated","insufficient_crystals")
missing=[token for token in required if token not in source]
if missing: raise SystemExit(f"missing_contract_tokens:{missing}")
for forbidden in ("sqlite3","aiogram","telegram"):
    if forbidden in source.lower(): raise SystemExit(f"forbidden_dependency:{forbidden}")
print("STAGE_21_10_1C_CRYSTAL_WALLET_LEDGER_SMOKE: PASS")
'''


def run_ci(root, env):
    temporary = root / "reports/.stage_21_10_2c_ci.tmp.json"
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
        print("[1/10] [PASS] Stage 21.10.2b zero-unresolved implementation prerequisite verified.")
        print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
        before = protected(root)
        folder, state = backup(root)
        print("[3/10] [PASS] All mutation targets backed up before production mutation.")
        write(root, APP, app_text())
        write(root, TEST, test_text())
        write(root, TOOL, tool_text())
        print("[4/10] [PASS] CrystalWalletLedgerService, immutable ledger DTOs and ports implemented.")
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
        print("[6/10] [PASS] Integer credit/debit, idempotency, exact-once compensation, rollback and restart tests passed.")
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
            "application_service": "CrystalWalletLedgerService",
            "implementation": APP.as_posix(),
            "tests": TEST.as_posix(),
            "implemented": [
                "integer_amounts", "account_level_user_id", "non_negative_balance",
                "fail_closed_debit", "stable_idempotency_key", "append_only_ledger",
                "same_payload_idempotent_replay", "changed_payload_conflict",
                "exact_once_compensation", "compensation_of_compensation_forbidden",
                "caller_owned_unit_of_work", "single_commit", "atomic_rollback",
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
        write(root, DOC, '''# Stage 21.10.2c - Crystal Wallet/Ledger implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Canonical owner: `CrystalWalletLedgerService`
- Amount representation: positive integer crystals
- Non-negative balance: **enforced**
- Stable idempotency key and append-only ledger: **implemented**
- Same-payload replay and exact-once compensation: **idempotent**
- Changed-payload replay: **conflict**
- Single caller-owned commit and atomic rollback: **implemented**
- SQLite / production persistence: **NOT_CONNECTED**
- Runtime / Telegram: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

The implementation is API-ready only. Production adapters and runtime wiring remain outside Stage 21.10.2c.
''')
        print("[9/10] [PASS] Machine report and Markdown implementation documentation written.")
        expected = {rel.as_posix() for rel in TARGETS}
        git(root, "add", "--", APP.as_posix(), TEST.as_posix(), TOOL.as_posix())
        git(root, "add", "-f", "--", SELF.as_posix(), REPORT.as_posix(), DOC.as_posix())
        staged = {line.strip().replace("\\", "/") for line in git(root, "diff", "--cached", "--name-only").stdout.splitlines() if line.strip()}
        if staged != expected:
            raise PatchError(f"staging_mismatch:{sorted(staged)}")
        commit_result = git(root, "commit", "-m", "Stage 21.10.2c: implement Crystal Wallet/Ledger", check=False)
        if commit_result.returncode:
            raise PatchError(f"commit_failed:{commit_result.stdout}:{commit_result.stderr}")
        commit = git(root, "rev-parse", "HEAD").stdout.strip()
        changed = {line.strip().replace("\\", "/") for line in git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.splitlines() if line.strip()}
        if changed != expected:
            raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
        (root / FAILURE).unlink(missing_ok=True)
        print(f"[10/10] [PASS] Crystal Wallet/Ledger implementation committed: {commit}")
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
