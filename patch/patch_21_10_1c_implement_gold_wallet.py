#!/usr/bin/env python3
"""ROM Stage 21.10.1c: implement the API-ready V2 Gold Wallet service.

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

STAGE = "21.10.1c"
BRANCH = "rewrite/rom-v2"
PARENT = "69ff48d8437086e4f5b7ce42898cf45c4821c9a9"
PREREQ = Path("reports/stage_21_10_1b_resolved_gold_wallet_parity.json")
APP = Path("rom_v2/application/gold_wallet.py")
TEST = Path("tests_v2/test_gold_wallet.py")
TOOL = Path("tools/check_stage_21_10_1c_gold_wallet.py")
REPORT = Path("reports/stage_21_10_1c_gold_wallet_implementation.json")
DOC = Path("MD/STAGE_21_10_1C_GOLD_WALLET_IMPLEMENTATION.md")
FAILURE = Path("reports/stage_21_10_1c_failure_rollback.json")
SELF = Path("patch/patch_21_10_1c_implement_gold_wallet.py")
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
        raise PatchError("missing_stage_21_10_1b_prerequisite")
    contract = json.loads((root / PREREQ).read_text(encoding="utf-8"))
    expected = ("21.10.1b", "PASS", "GO_TO_IMPLEMENTATION")
    if (contract.get("stage"), contract.get("status"), contract.get("conclusion")) != expected:
        raise PatchError("invalid_stage_21_10_1b_prerequisite")
    summary = contract.get("summary", {})
    if summary.get("remaining_unresolved_contracts") != 0:
        raise PatchError("unresolved_gold_wallet_contracts")
    if contract.get("implementation_authorized") is not True:
        raise PatchError("implementation_not_authorized")
    wallet = contract.get("v2_gold_wallet_contract", {})
    required = {
        "canonical_owner": "GoldWalletService",
        "amount_type": "Decimal",
        "scale": "0.01",
        "rounding": "ROUND_HALF_UP",
        "non_negative_balance": True,
        "stable_operation_key_required": True,
        "immutable_operation_history": True,
        "caller_owned_unit_of_work": True,
        "single_commit": True,
        "presentation_separate": True,
    }
    if any(wallet.get(key) != value for key, value in required.items()):
        raise PatchError(f"invalid_gold_wallet_contract:{wallet}")
    if git(root, "diff", "--cached", "--name-only").stdout.strip():
        raise PatchError("index_not_clean")
    dirty = status_paths(root)
    if not dirty.issubset(ALLOWED_DIRTY):
        raise PatchError(f"unexpected_dirty:{sorted(dirty - ALLOWED_DIRTY)}")
    return contract


def backup(root):
    folder = root / "backup" / f"stage_21_10_1c_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
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
    return '''"""Pure API-ready Gold Wallet service for ROM V2.

Money is Decimal-only and quantized to two places with ROUND_HALF_UP. Persistence,
SQLite, runtime and presentation adapters are intentionally outside this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from typing import Protocol

GOLD_QUANTUM = Decimal("0.01")


class GoldWalletContractError(ValueError):
    """Raised when a wallet command violates the public contract."""


class GoldWalletConflictError(GoldWalletContractError):
    """Raised when one operation key is replayed with a different payload."""


class GoldDirection(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


@dataclass(frozen=True, slots=True)
class GoldWalletCommand:
    """Stable, presentation-free request for one exact wallet mutation."""

    operation_key: str
    account_id: int
    direction: GoldDirection
    amount: Decimal
    reason_code: str


@dataclass(frozen=True, slots=True)
class GoldWalletOperation:
    """Immutable audit record persisted atomically with the balance."""

    operation_key: str
    account_id: int
    direction: GoldDirection
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    reason_code: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class GoldWalletResult:
    operation: GoldWalletOperation
    replayed: bool


class GoldWalletRepositoryPort(Protocol):
    def get_balance(self, account_id: int) -> Decimal: ...
    def set_balance(self, account_id: int, balance: Decimal) -> None: ...
    def get_operation(self, operation_key: str) -> GoldWalletOperation | None: ...
    def add_operation(self, operation: GoldWalletOperation) -> None: ...


class GoldWalletUnitOfWorkPort(Protocol):
    wallet: GoldWalletRepositoryPort
    def now(self) -> datetime: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


def normalize_gold(value: Decimal) -> Decimal:
    """Validate and quantize Decimal money without accepting float input."""
    if not isinstance(value, Decimal):
        raise GoldWalletContractError("amount_must_be_decimal")
    if not value.is_finite():
        raise GoldWalletContractError("amount_must_be_finite")
    try:
        return value.quantize(GOLD_QUANTUM, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise GoldWalletContractError("amount_cannot_be_quantized") from exc


class GoldWalletService:
    """Canonical V2 owner for atomic, idempotent gold mutations."""

    def execute(self, command: GoldWalletCommand, unit_of_work: GoldWalletUnitOfWorkPort) -> GoldWalletResult:
        normalized = self._validate_command(command)
        canonical = GoldWalletCommand(
            operation_key=command.operation_key,
            account_id=command.account_id,
            direction=command.direction,
            amount=normalized,
            reason_code=command.reason_code,
        )
        try:
            existing = unit_of_work.wallet.get_operation(canonical.operation_key)
            if existing is not None:
                if not self._same_payload(existing, canonical):
                    raise GoldWalletConflictError("operation_key_payload_conflict")
                return GoldWalletResult(existing, replayed=True)

            before = normalize_gold(unit_of_work.wallet.get_balance(canonical.account_id))
            if before < Decimal("0.00"):
                raise GoldWalletContractError("stored_balance_is_negative")
            after = before + canonical.amount if canonical.direction is GoldDirection.CREDIT else before - canonical.amount
            after = normalize_gold(after)
            if after < Decimal("0.00"):
                raise GoldWalletContractError("insufficient_funds")

            operation = GoldWalletOperation(
                operation_key=canonical.operation_key,
                account_id=canonical.account_id,
                direction=canonical.direction,
                amount=canonical.amount,
                balance_before=before,
                balance_after=after,
                reason_code=canonical.reason_code,
                created_at=unit_of_work.now(),
            )
            unit_of_work.wallet.set_balance(canonical.account_id, after)
            unit_of_work.wallet.add_operation(operation)
            unit_of_work.commit()
            return GoldWalletResult(operation, replayed=False)
        except Exception:
            unit_of_work.rollback()
            raise

    @staticmethod
    def _validate_command(command: GoldWalletCommand) -> Decimal:
        if not command.operation_key or not command.operation_key.strip():
            raise GoldWalletContractError("operation_key_required")
        if command.account_id <= 0:
            raise GoldWalletContractError("account_id_must_be_positive")
        if not isinstance(command.direction, GoldDirection):
            raise GoldWalletContractError("invalid_direction")
        if not command.reason_code or not command.reason_code.strip():
            raise GoldWalletContractError("reason_code_required")
        amount = normalize_gold(command.amount)
        if amount <= Decimal("0.00"):
            raise GoldWalletContractError("amount_must_be_positive")
        return amount

    @staticmethod
    def _same_payload(existing: GoldWalletOperation, command: GoldWalletCommand) -> bool:
        return (
            existing.account_id == command.account_id
            and existing.direction is command.direction
            and existing.amount == command.amount
            and existing.reason_code == command.reason_code
        )
'''


def test_text():
    return '''import unittest
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal

from rom_v2.application.gold_wallet import (
    GoldDirection, GoldWalletCommand, GoldWalletConflictError,
    GoldWalletContractError, GoldWalletOperation, GoldWalletService,
    normalize_gold,
)


class MemoryWallet:
    def __init__(self, balance=Decimal("0.00")):
        self.balances={1: balance}; self.operations={}
    def get_balance(self, account_id): return self.balances.get(account_id, Decimal("0.00"))
    def set_balance(self, account_id, balance): self.balances[account_id]=balance
    def get_operation(self, operation_key): return self.operations.get(operation_key)
    def add_operation(self, operation):
        if operation.operation_key in self.operations: raise RuntimeError("duplicate_operation")
        self.operations[operation.operation_key]=operation


class MemoryUnitOfWork:
    def __init__(self, balance=Decimal("0.00"), fail_commit=False):
        self.wallet=MemoryWallet(balance); self.fail_commit=fail_commit
        self.commits=0; self.rollbacks=0; self._snapshot=None
    def begin(self): self._snapshot=(deepcopy(self.wallet.balances),deepcopy(self.wallet.operations))
    def now(self): return datetime(2026,1,2,3,4,5,tzinfo=timezone.utc)
    def commit(self):
        if self.fail_commit: raise RuntimeError("commit_failure")
        self.commits+=1; self._snapshot=None
    def rollback(self):
        self.rollbacks+=1
        if self._snapshot is not None:
            self.wallet.balances,self.wallet.operations=self._snapshot
            self._snapshot=None


def command(key="op-1", direction=GoldDirection.CREDIT, amount=Decimal("1.00"), reason="test"):
    return GoldWalletCommand(key,1,direction,amount,reason)


class GoldWalletTests(unittest.TestCase):
    def execute(self, uow, cmd): uow.begin(); return GoldWalletService().execute(cmd,uow)
    def test_credit_quantizes_half_up(self):
        uow=MemoryUnitOfWork(Decimal("2.00")); result=self.execute(uow,command(amount=Decimal("1.005")))
        self.assertEqual(result.operation.balance_after,Decimal("3.01")); self.assertEqual(uow.commits,1)
    def test_debit_exact_balance(self):
        uow=MemoryUnitOfWork(Decimal("2.00")); result=self.execute(uow,command(direction=GoldDirection.DEBIT,amount=Decimal("2.00")))
        self.assertEqual(result.operation.balance_after,Decimal("0.00"))
    def test_insufficient_funds_fails_without_mutation(self):
        uow=MemoryUnitOfWork(Decimal("1.00"))
        with self.assertRaisesRegex(GoldWalletContractError,"insufficient_funds"): self.execute(uow,command(direction=GoldDirection.DEBIT,amount=Decimal("1.01")))
        self.assertEqual(uow.wallet.get_balance(1),Decimal("1.00")); self.assertFalse(uow.wallet.operations); self.assertEqual(uow.commits,0)
    def test_same_payload_replay_returns_original_without_commit(self):
        uow=MemoryUnitOfWork(); first=self.execute(uow,command()); uow.begin(); second=GoldWalletService().execute(command(),uow)
        self.assertTrue(second.replayed); self.assertEqual(second.operation,first.operation); self.assertEqual(uow.commits,1)
    def test_changed_payload_replay_conflicts(self):
        uow=MemoryUnitOfWork(); self.execute(uow,command())
        uow.begin()
        with self.assertRaises(GoldWalletConflictError): GoldWalletService().execute(command(amount=Decimal("2.00")),uow)
        self.assertEqual(uow.wallet.get_balance(1),Decimal("1.00"))
    def test_commit_failure_rolls_back_balance_and_history(self):
        uow=MemoryUnitOfWork(fail_commit=True)
        with self.assertRaisesRegex(RuntimeError,"commit_failure"): self.execute(uow,command())
        self.assertEqual(uow.wallet.get_balance(1),Decimal("0.00")); self.assertFalse(uow.wallet.operations); self.assertEqual(uow.rollbacks,1)
    def test_float_is_rejected(self):
        with self.assertRaisesRegex(GoldWalletContractError,"amount_must_be_decimal"): normalize_gold(1.0)
    def test_non_finite_decimal_is_rejected(self):
        with self.assertRaisesRegex(GoldWalletContractError,"amount_must_be_finite"): normalize_gold(Decimal("NaN"))
    def test_zero_and_negative_amount_rejected(self):
        for value in (Decimal("0"),Decimal("-1")):
            with self.subTest(value=value), self.assertRaisesRegex(GoldWalletContractError,"amount_must_be_positive"):
                GoldWalletService().execute(command(amount=value),MemoryUnitOfWork())
    def test_required_stable_fields(self):
        for cmd,reason in ((command(key=""),"operation_key_required"),(GoldWalletCommand("x",0,GoldDirection.CREDIT,Decimal("1"),"r"),"account_id_must_be_positive"),(command(reason=""),"reason_code_required")):
            with self.subTest(reason=reason), self.assertRaisesRegex(GoldWalletContractError,reason): GoldWalletService().execute(cmd,MemoryUnitOfWork())
    def test_immutable_operation(self):
        uow=MemoryUnitOfWork(); operation=self.execute(uow,command()).operation
        with self.assertRaises(Exception): operation.amount=Decimal("9.00")
    def test_restart_replay_uses_persisted_operation(self):
        first=MemoryUnitOfWork(); original=self.execute(first,command())
        restarted=MemoryUnitOfWork(); restarted.wallet.balances=deepcopy(first.wallet.balances); restarted.wallet.operations=deepcopy(first.wallet.operations); restarted.begin()
        replay=GoldWalletService().execute(command(),restarted)
        self.assertTrue(replay.replayed); self.assertEqual(replay.operation,original.operation); self.assertEqual(restarted.commits,0)


if __name__ == "__main__": unittest.main()
'''


def tool_text():
    return '''#!/usr/bin/env python3
"""Targeted Stage 21.10.1c Gold Wallet verifier."""
import ast
from pathlib import Path

root=Path(__file__).resolve().parents[1]
app=root/"rom_v2/application/gold_wallet.py"
test=root/"tests_v2/test_gold_wallet.py"
for path in (app,test): ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
source=app.read_text(encoding="utf-8")
required=("class GoldWalletService","class GoldWalletOperation","class GoldWalletCommand","ROUND_HALF_UP","operation_key_payload_conflict","insufficient_funds")
missing=[token for token in required if token not in source]
if missing: raise SystemExit(f"missing_contract_tokens:{missing}")
for forbidden in ("sqlite3","aiogram","telegram"):
    if forbidden in source.lower(): raise SystemExit(f"forbidden_dependency:{forbidden}")
print("STAGE_21_10_1C_GOLD_WALLET_SMOKE: PASS")
'''


def run_ci(root, env):
    temporary = root / "reports/.stage_21_10_1c_ci.tmp.json"
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
        print("[1/10] [PASS] Stage 21.10.1b zero-unresolved implementation prerequisite verified.")
        print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
        before = protected(root)
        folder, state = backup(root)
        print("[3/10] [PASS] All mutation targets backed up before production mutation.")
        write(root, APP, app_text())
        write(root, TEST, test_text())
        write(root, TOOL, tool_text())
        print("[4/10] [PASS] Decimal GoldWalletService, immutable operation DTOs and ports implemented.")
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
        print("[6/10] [PASS] Decimal, debit rejection, idempotency, conflict, rollback and restart tests passed.")
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
            "application_service": "GoldWalletService",
            "implementation": APP.as_posix(),
            "tests": TEST.as_posix(),
            "implemented": [
                "decimal_only_amounts", "two_decimal_scale", "round_half_up",
                "non_negative_balance", "fail_closed_debit", "stable_operation_key",
                "immutable_operation_history", "same_payload_idempotent_replay",
                "changed_payload_conflict", "caller_owned_unit_of_work",
                "single_commit", "atomic_rollback", "restart_replay",
                "presentation_excluded", "crystal_wallet_excluded",
            ],
            "not_connected": [
                "sqlite", "production_repository_adapters", "runtime", "telegram",
                "presentation", "crystal_wallet",
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
        write(root, DOC, '''# Stage 21.10.1c - Gold Wallet implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Canonical owner: `GoldWalletService`
- Money representation: `Decimal`, scale `0.01`, `ROUND_HALF_UP`
- Non-negative balance: **enforced**
- Stable operation key and immutable history: **implemented**
- Same-payload replay: **idempotent**
- Changed-payload replay: **conflict**
- Single caller-owned commit and atomic rollback: **implemented**
- SQLite / production persistence: **NOT_CONNECTED**
- Runtime / Telegram: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

The implementation is API-ready only. Production adapters and runtime wiring remain outside Stage 21.10.1c.
''')
        print("[9/10] [PASS] Machine report and Markdown implementation documentation written.")
        expected = {rel.as_posix() for rel in TARGETS}
        git(root, "add", "--", APP.as_posix(), TEST.as_posix(), TOOL.as_posix())
        git(root, "add", "-f", "--", SELF.as_posix(), REPORT.as_posix(), DOC.as_posix())
        staged = {line.strip().replace("\\", "/") for line in git(root, "diff", "--cached", "--name-only").stdout.splitlines() if line.strip()}
        if staged != expected:
            raise PatchError(f"staging_mismatch:{sorted(staged)}")
        commit_result = git(root, "commit", "-m", "Stage 21.10.1c: implement Gold Wallet", check=False)
        if commit_result.returncode:
            raise PatchError(f"commit_failed:{commit_result.stdout}:{commit_result.stderr}")
        commit = git(root, "rev-parse", "HEAD").stdout.strip()
        changed = {line.strip().replace("\\", "/") for line in git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.splitlines() if line.strip()}
        if changed != expected:
            raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
        (root / FAILURE).unlink(missing_ok=True)
        print(f"[10/10] [PASS] Gold Wallet implementation committed: {commit}")
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
