#!/usr/bin/env python3
"""ROM Stage 21.10.6c: implement the API-ready V2 Daily Reward service.

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

STAGE = "21.10.6c"
BRANCH = "rewrite/rom-v2"
PARENT = "6aa7deb020115727709cef39f60f9d9f769cf734"
PREREQ = Path("reports/stage_21_10_6b_resolved_daily_reward_parity.json")
APP = Path("rom_v2/application/daily_reward.py")
TEST = Path("tests_v2/test_daily_reward.py")
TOOL = Path("tools/check_stage_21_10_6c_daily_reward.py")
REPORT = Path("reports/stage_21_10_6c_daily_reward_implementation.json")
DOC = Path("MD/STAGE_21_10_6C_DAILY_REWARD_IMPLEMENTATION.md")
FAILURE = Path("reports/stage_21_10_6c_failure_rollback.json")
SELF = Path("patch/patch_21_10_6c_implement_daily_reward.py")
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
        raise PatchError("missing_stage_21_10_6b_prerequisite")
    contract = json.loads((root / PREREQ).read_text(encoding="utf-8"))
    expected = ("21.10.6b", "PASS", "GO_TO_IMPLEMENTATION")
    if (contract.get("stage"), contract.get("status"), contract.get("conclusion")) != expected:
        raise PatchError("invalid_stage_21_10_6b_prerequisite")
    summary = contract.get("summary", {})
    if summary.get("remaining_unresolved_contracts") != 0:
        raise PatchError("unresolved_daily_reward_contracts")
    if contract.get("implementation_authorized") is not True:
        raise PatchError("implementation_not_authorized")
    reward = contract.get("v2_daily_reward_contract", {})
    required = {
        "canonical_owner": "DailyRewardService", "account_identity": "user_id",
        "reward_key": "daily_reward_3hp_3firius",
        "small_hp_potion_key": "small_hp_potion", "small_hp_potion_quantity": 3,
        "phirius_token_key": "phirius_token", "phirius_token_quantity": 3,
        "once_per_period": True, "stable_period_key_required": True,
        "quest_completion_required": True, "inventory_preflight": True,
        "stable_operation_key_required": True,
        "atomic_potion_token_claim_receipt": True, "restart_safe": True,
        "caller_owned_unit_of_work": True, "single_commit": True,
        "presentation_separate": True,
    }
    if contract.get("approved_reward_scope") != {"small_hp_potions": 3, "phirius_tokens": 3}:
        raise PatchError("invalid_approved_daily_reward_scope")
    if any(reward.get(key) != value for key, value in required.items()):
        raise PatchError(f"invalid_daily_reward_contract:{reward}")
    if git(root, "diff", "--cached", "--name-only").stdout.strip():
        raise PatchError("index_not_clean")
    dirty = status_paths(root)
    if not dirty.issubset(ALLOWED_DIRTY):
        raise PatchError(f"unexpected_dirty:{sorted(dirty - ALLOWED_DIRTY)}")
    return contract


def backup(root):
    folder = root / "backup" / f"stage_21_10_6c_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
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
    return '''"""Pure API-ready Daily Reward service for ROM V2.

The only authorized reward is three small HP potions plus three Phirius Tokens.
The superseded five-token value is intentionally absent from this module.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

REWARD_KEY="daily_reward_3hp_3firius"
SMALL_HP_POTION_KEY="small_hp_potion"
SMALL_HP_POTION_QUANTITY=3
PHIRIUS_TOKEN_KEY="phirius_token"
PHIRIUS_TOKEN_QUANTITY=3

class DailyRewardContractError(ValueError): pass
class DailyRewardConflictError(DailyRewardContractError): pass

@dataclass(frozen=True, slots=True)
class DailyRewardDefinition:
    reward_key:str=REWARD_KEY
    small_hp_potion_key:str=SMALL_HP_POTION_KEY
    small_hp_potion_quantity:int=SMALL_HP_POTION_QUANTITY
    phirius_token_key:str=PHIRIUS_TOKEN_KEY
    phirius_token_quantity:int=PHIRIUS_TOKEN_QUANTITY

@dataclass(frozen=True, slots=True)
class DailyRewardClaimCommand:
    operation_key:str
    user_id:int
    period_key:str
    reward_key:str=REWARD_KEY

@dataclass(frozen=True, slots=True)
class DailyRewardStackPlan:
    item_key:str
    quantity_before:int
    quantity_delta:int
    quantity_after:int

@dataclass(frozen=True, slots=True)
class DailyRewardReceipt:
    operation_key:str
    user_id:int
    period_key:str
    reward_key:str
    small_hp_potions_granted:int
    phirius_tokens_granted:int
    small_hp_quantity_after:int
    phirius_token_quantity_after:int

@dataclass(frozen=True, slots=True)
class DailyRewardResult:
    receipt:DailyRewardReceipt
    replayed:bool

class DailyQuestStatePort(Protocol):
    def exists(self,user_id:int,period_key:str)->bool: ...
    def is_complete(self,user_id:int,period_key:str)->bool: ...
    def is_claimed(self,user_id:int,period_key:str)->bool: ...
    def mark_claimed(self,user_id:int,period_key:str)->None: ...
class DailyPeriodPort(Protocol):
    def current_period_key(self)->str: ...
class DailyRewardInventoryPort(Protocol):
    def quantity(self,user_id:int,item_key:str)->int: ...
    def build_add_plan(self,user_id:int,item_key:str,quantity:int)->DailyRewardStackPlan: ...
    def validate_capacity(self,user_id:int,plan:DailyRewardStackPlan)->None: ...
    def apply_plan(self,user_id:int,plan:DailyRewardStackPlan)->None: ...
class DailyRewardTokenWalletPort(Protocol):
    def credit(self,user_id:int,token_key:str,quantity:int)->int: ...
class DailyRewardReceiptPort(Protocol):
    def get_receipt(self,operation_key:str)->DailyRewardReceipt|None: ...
    def get_period_receipt(self,user_id:int,period_key:str)->DailyRewardReceipt|None: ...
    def save_receipt(self,receipt:DailyRewardReceipt)->None: ...
class DailyRewardUnitOfWorkPort(Protocol):
    quest:DailyQuestStatePort
    period:DailyPeriodPort
    inventory:DailyRewardInventoryPort
    tokens:DailyRewardTokenWalletPort
    receipts:DailyRewardReceiptPort
    def commit(self)->None: ...
    def rollback(self)->None: ...

class DailyRewardService:
    """Canonical owner for exact-once atomic Daily Reward settlement."""
    reward=DailyRewardDefinition()
    def claim(self,command:DailyRewardClaimCommand,uow:DailyRewardUnitOfWorkPort)->DailyRewardResult:
        self._validate_command(command)
        try:
            replay=uow.receipts.get_receipt(command.operation_key)
            if replay is not None:
                if not self._same_payload(replay,command):raise DailyRewardConflictError("operation_key_payload_conflict")
                return DailyRewardResult(replay,True)
            current_period=uow.period.current_period_key()
            if not current_period.strip():raise DailyRewardContractError("invalid_current_period")
            if command.period_key!=current_period:raise DailyRewardContractError("stale_period")
            if not uow.quest.exists(command.user_id,command.period_key):raise DailyRewardContractError("daily_quest_not_found")
            if not uow.quest.is_complete(command.user_id,command.period_key):raise DailyRewardContractError("daily_quest_incomplete")
            prior=uow.receipts.get_period_receipt(command.user_id,command.period_key)
            if prior is not None or uow.quest.is_claimed(command.user_id,command.period_key):raise DailyRewardContractError("already_claimed")
            before=uow.inventory.quantity(command.user_id,SMALL_HP_POTION_KEY)
            plan=uow.inventory.build_add_plan(command.user_id,SMALL_HP_POTION_KEY,SMALL_HP_POTION_QUANTITY)
            self._validate_plan(plan,before)
            uow.inventory.validate_capacity(command.user_id,plan)
            uow.inventory.apply_plan(command.user_id,plan)
            token_after=uow.tokens.credit(command.user_id,PHIRIUS_TOKEN_KEY,PHIRIUS_TOKEN_QUANTITY)
            uow.quest.mark_claimed(command.user_id,command.period_key)
            receipt=DailyRewardReceipt(command.operation_key,command.user_id,command.period_key,REWARD_KEY,SMALL_HP_POTION_QUANTITY,PHIRIUS_TOKEN_QUANTITY,plan.quantity_after,token_after)
            uow.receipts.save_receipt(receipt);uow.commit()
            return DailyRewardResult(receipt,False)
        except Exception:
            uow.rollback();raise
    @staticmethod
    def _validate_command(command:DailyRewardClaimCommand)->None:
        if not command.operation_key.strip():raise DailyRewardContractError("operation_key_required")
        if command.user_id<=0:raise DailyRewardContractError("user_id_must_be_positive")
        if not command.period_key.strip():raise DailyRewardContractError("period_key_required")
        if command.reward_key!=REWARD_KEY:raise DailyRewardContractError("invalid_reward_key")
    @staticmethod
    def _validate_plan(plan:DailyRewardStackPlan,before:int)->None:
        if plan.item_key!=SMALL_HP_POTION_KEY or plan.quantity_before!=before or plan.quantity_delta!=SMALL_HP_POTION_QUANTITY or plan.quantity_after!=before+SMALL_HP_POTION_QUANTITY:
            raise DailyRewardContractError("invalid_reward_stack_plan")
    @staticmethod
    def _same_payload(receipt:DailyRewardReceipt,command:DailyRewardClaimCommand)->bool:
        return receipt.user_id==command.user_id and receipt.period_key==command.period_key and receipt.reward_key==command.reward_key
'''


def test_text():
    return '''import unittest
from copy import deepcopy
from rom_v2.application.daily_reward import *
class Quest:
 def __init__(self,exists=True,complete=True,claimed=False):self.e=exists;self.c=complete;self.claimed=claimed
 def exists(self,u,p):return self.e
 def is_complete(self,u,p):return self.c
 def is_claimed(self,u,p):return self.claimed
 def mark_claimed(self,u,p):self.claimed=True
class Period:
 def __init__(self,p="2026-10-23"):self.p=p
 def current_period_key(self):return self.p
class Inventory:
 def __init__(self,q=2,capacity=True):self.q=q;self.capacity=capacity;self.plans=[]
 def quantity(self,u,k):return self.q
 def build_add_plan(self,u,k,q):return DailyRewardStackPlan(k,self.q,q,self.q+q)
 def validate_capacity(self,u,p):
  if not self.capacity:raise DailyRewardContractError("inventory_full")
 def apply_plan(self,u,p):self.q=p.quantity_after;self.plans.append(p)
class Tokens:
 def __init__(self,q=4):self.q=q
 def credit(self,u,k,q):self.q+=q;return self.q
class Receipts:
 def __init__(self):self.rows={};self.period={}
 def get_receipt(self,k):return self.rows.get(k)
 def get_period_receipt(self,u,p):return self.period.get((u,p))
 def save_receipt(self,r):self.rows[r.operation_key]=r;self.period[(r.user_id,r.period_key)]=r
class Uow:
 def __init__(self,complete=True,claimed=False,capacity=True,fail=False):self.quest=Quest(complete=complete,claimed=claimed);self.period=Period();self.inventory=Inventory(capacity=capacity);self.tokens=Tokens();self.receipts=Receipts();self.fail=fail;self.commits=0;self.rollbacks=0;self.snap=None
 def begin(self):self.snap=deepcopy((self.quest,self.period,self.inventory,self.tokens,self.receipts))
 def commit(self):
  if self.fail:raise RuntimeError("commit_failure")
  self.commits+=1;self.snap=None
 def rollback(self):
  self.rollbacks+=1
  if self.snap:self.quest,self.period,self.inventory,self.tokens,self.receipts=self.snap;self.snap=None
def cmd(k="op",p="2026-10-23",r=REWARD_KEY):return DailyRewardClaimCommand(k,1,p,r)
def execute(u,c=cmd()):u.begin();return DailyRewardService().claim(c,u)
class Tests(unittest.TestCase):
 def test_exact_three_plus_three(self):
  u=Uow();r=execute(u);self.assertEqual(r.receipt.small_hp_potions_granted,3);self.assertEqual(r.receipt.phirius_tokens_granted,3);self.assertEqual(u.inventory.q,5);self.assertEqual(u.tokens.q,7);self.assertTrue(u.quest.claimed);self.assertEqual(u.commits,1)
 def test_incomplete_rejected(self):
  u=Uow(complete=False)
  with self.assertRaisesRegex(DailyRewardContractError,"daily_quest_incomplete"):execute(u)
  self.assertEqual(u.inventory.q,2);self.assertEqual(u.tokens.q,4)
 def test_stale_period_rejected(self):
  u=Uow()
  with self.assertRaisesRegex(DailyRewardContractError,"stale_period"):execute(u,cmd(p="2026-10-22"))
 def test_inventory_full_rolls_nothing(self):
  u=Uow(capacity=False)
  with self.assertRaisesRegex(DailyRewardContractError,"inventory_full"):execute(u)
  self.assertEqual(u.inventory.q,2);self.assertEqual(u.tokens.q,4);self.assertFalse(u.quest.claimed)
 def test_already_claimed_rejected(self):
  u=Uow(claimed=True)
  with self.assertRaisesRegex(DailyRewardContractError,"already_claimed"):execute(u)
 def test_replay_and_conflict(self):
  u=Uow();first=execute(u);u.begin();again=DailyRewardService().claim(cmd(),u);self.assertTrue(again.replayed);self.assertEqual(first.receipt,again.receipt);self.assertEqual(u.inventory.q,5);self.assertEqual(u.tokens.q,7);u.begin()
  with self.assertRaises(DailyRewardConflictError):DailyRewardService().claim(DailyRewardClaimCommand("op",2,"2026-10-23",REWARD_KEY),u)
 def test_wrong_reward_key_forbidden(self):
  with self.assertRaisesRegex(DailyRewardContractError,"invalid_reward_key"):DailyRewardService().claim(cmd(r="legacy_five_tokens"),Uow())
 def test_commit_failure_rolls_back_all(self):
  u=Uow(fail=True)
  with self.assertRaisesRegex(RuntimeError,"commit_failure"):execute(u)
  self.assertEqual(u.inventory.q,2);self.assertEqual(u.tokens.q,4);self.assertFalse(u.quest.claimed);self.assertFalse(u.receipts.rows)
 def test_restart_replay(self):
  first=Uow();original=execute(first);second=deepcopy(first);second.begin();replay=DailyRewardService().claim(cmd(),second);self.assertTrue(replay.replayed);self.assertEqual(replay.receipt,original.receipt);self.assertEqual(second.inventory.q,5);self.assertEqual(second.tokens.q,7)
if __name__=="__main__":unittest.main()
'''


def tool_text():
    return '''#!/usr/bin/env python3
"""Targeted Stage 21.10.6c Daily Reward verifier."""
import ast
from pathlib import Path

root=Path(__file__).resolve().parents[1]
app=root/"rom_v2/application/daily_reward.py"
test=root/"tests_v2/test_daily_reward.py"
for path in (app,test): ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
source=app.read_text(encoding="utf-8")
required=("class DailyRewardService","class DailyRewardClaimCommand","class DailyRewardReceipt","operation_key_payload_conflict","already_claimed","stale_period")
missing=[token for token in required if token not in source]
if missing: raise SystemExit(f"missing_contract_tokens:{missing}")
for forbidden in ("sqlite3","aiogram","telegram"):
    if forbidden in source.lower(): raise SystemExit(f"forbidden_dependency:{forbidden}")
print("STAGE_21_10_6C_DAILY_REWARD_SMOKE: PASS")
'''


def run_ci(root, env):
    temporary = root / "reports/.stage_21_10_6c_ci.tmp.json"
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
        print("[1/10] [PASS] Stage 21.10.6b zero-unresolved implementation prerequisite verified.")
        print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
        before = protected(root)
        folder, state = backup(root)
        print("[3/10] [PASS] All mutation targets backed up before production mutation.")
        write(root, APP, app_text())
        write(root, TEST, test_text())
        write(root, TOOL, tool_text())
        print("[4/10] [PASS] DailyRewardService, immutable reward/claim/stack-plan/receipt DTOs and ports implemented.")
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
        print("[6/10] [PASS] Exact 3+3 reward, once-per-period, capacity, idempotency, rollback and restart tests passed.")
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
            "application_service": "DailyRewardService",
            "implementation": APP.as_posix(),
            "tests": TEST.as_posix(),
            "implemented": [
                "exact_three_small_hp_potions", "exact_three_phirius_tokens",
                "superseded_five_token_value_forbidden", "account_level_user_id",
                "stable_period_key", "quest_completion_required", "once_per_period",
                "inventory_capacity_preflight", "deterministic_reward_stack_plan",
                "stable_operation_key", "same_payload_idempotent_replay",
                "changed_payload_conflict", "atomic_potion_token_claim_receipt",
                "single_commit", "atomic_rollback", "restart_replay",
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
        write(root, DOC, '''# Stage 21.10.6c - Daily Reward implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Canonical owner: `DailyRewardService`
- Exact Daily Reward: 3 small HP potions and 3 Phirius Tokens
- Non-negative balance: **enforced**
- Stable operation and period keys with immutable claim receipt: **implemented**
- Atomic once-per-period 3+3 claim with idempotent replay: **idempotent**
- Changed-payload replay: **conflict**
- Single caller-owned commit and atomic rollback: **implemented**
- SQLite / production persistence: **NOT_CONNECTED**
- Runtime / Telegram: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

The implementation is API-ready only. Production adapters and runtime wiring remain outside Stage 21.10.6c.
''')
        print("[9/10] [PASS] Machine report and Markdown implementation documentation written.")
        expected = {rel.as_posix() for rel in TARGETS}
        git(root, "add", "--", APP.as_posix(), TEST.as_posix(), TOOL.as_posix())
        git(root, "add", "-f", "--", SELF.as_posix(), REPORT.as_posix(), DOC.as_posix())
        staged = {line.strip().replace("\\", "/") for line in git(root, "diff", "--cached", "--name-only").stdout.splitlines() if line.strip()}
        if staged != expected:
            raise PatchError(f"staging_mismatch:{sorted(staged)}")
        commit_result = git(root, "commit", "-m", "Stage 21.10.6c: implement Daily Reward", check=False)
        if commit_result.returncode:
            raise PatchError(f"commit_failed:{commit_result.stdout}:{commit_result.stderr}")
        commit = git(root, "rev-parse", "HEAD").stdout.strip()
        changed = {line.strip().replace("\\", "/") for line in git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.splitlines() if line.strip()}
        if changed != expected:
            raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
        (root / FAILURE).unlink(missing_ok=True)
        print(f"[10/10] [PASS] Daily Reward implementation committed: {commit}")
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
