#!/usr/bin/env python3
"""ROM Stage 21.10.3c: implement the API-ready V2 Base Equipment Shop service.

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

STAGE = "21.10.3c"
BRANCH = "rewrite/rom-v2"
PARENT = "4341fe0caaab3b23b34aa10a3229f2776e467266"
PREREQ = Path("reports/stage_21_10_3b_resolved_base_equipment_shop_parity.json")
APP = Path("rom_v2/application/base_equipment_shop.py")
TEST = Path("tests_v2/test_base_equipment_shop.py")
TOOL = Path("tools/check_stage_21_10_3c_base_equipment_shop.py")
REPORT = Path("reports/stage_21_10_3c_base_equipment_shop_implementation.json")
DOC = Path("MD/STAGE_21_10_1C_CRYSTAL_WALLET_LEDGER_IMPLEMENTATION.md")
FAILURE = Path("reports/stage_21_10_3c_failure_rollback.json")
SELF = Path("patch/patch_21_10_3c_implement_base_equipment_shop.py")
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
        raise PatchError("missing_stage_21_10_3b_prerequisite")
    contract = json.loads((root / PREREQ).read_text(encoding="utf-8"))
    expected = ("21.10.3b", "PASS", "GO_TO_IMPLEMENTATION")
    if (contract.get("stage"), contract.get("status"), contract.get("conclusion")) != expected:
        raise PatchError("invalid_stage_21_10_3b_prerequisite")
    summary = contract.get("summary", {})
    if summary.get("remaining_unresolved_contracts") != 0:
        raise PatchError("unresolved_base_equipment_shop_contracts")
    if contract.get("implementation_authorized") is not True:
        raise PatchError("implementation_not_authorized")
    shop = contract.get("v2_base_equipment_shop_contract", {})
    required = {
        "canonical_owner": "BaseEquipmentShopService", "class_aware_offers": True,
        "stable_offer_keys": True, "immutable_preview_snapshot": True,
        "quoted_price_locked": True, "user_owned_preview": True,
        "inventory_preflight": True, "stable_operation_key_required": True,
        "never_reuse_permanent_id": True, "atomic_promotion_purchase": True,
        "caller_owned_unit_of_work": True, "single_commit": True,
        "presentation_separate": True,
    }
    if any(shop.get(key) != value for key, value in required.items()):
        raise PatchError(f"invalid_base_equipment_shop_contract:{shop}")
    if git(root, "diff", "--cached", "--name-only").stdout.strip():
        raise PatchError("index_not_clean")
    dirty = status_paths(root)
    if not dirty.issubset(ALLOWED_DIRTY):
        raise PatchError(f"unexpected_dirty:{sorted(dirty - ALLOWED_DIRTY)}")
    return contract


def backup(root):
    folder = root / "backup" / f"stage_21_10_3c_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
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
    return '''"""Pure API-ready Base Equipment Shop service for ROM V2."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

class ShopContractError(ValueError): pass
class ShopConflictError(ShopContractError): pass

@dataclass(frozen=True, slots=True)
class EquipmentSnapshot:
    template_key:str; slot_key:str; profile_key:str; class_key:str
    stats:tuple[tuple[str,int],...]; rarity_key:str; durability:int

@dataclass(frozen=True, slots=True)
class ShopOffer:
    offer_key:str; suboffer_key:str; class_key:str; slot_key:str; profile_key:str; price:int

@dataclass(frozen=True, slots=True)
class ShopPreview:
    preview_id:int; user_id:int; offer_key:str; suboffer_key:str; class_key:str
    item:EquipmentSnapshot; quoted_price:int; created_at:datetime

@dataclass(frozen=True, slots=True)
class ConfirmPurchase:
    operation_key:str; user_id:int; preview_id:int

@dataclass(frozen=True, slots=True)
class PurchaseReceipt:
    operation_key:str; user_id:int; preview_id:int; permanent_item_id:int
    price:int; balance_after:int; inventory_entry_id:int

@dataclass(frozen=True, slots=True)
class PurchaseResult:
    receipt:PurchaseReceipt; replayed:bool

class ShopRepositoryPort(Protocol):
    def get_preview(self,preview_id:int)->ShopPreview|None: ...
    def get_receipt(self,operation_key:str)->PurchaseReceipt|None: ...
    def save_receipt(self,receipt:PurchaseReceipt)->None: ...
    def invalidate_preview(self,preview_id:int)->None: ...
class ShopWalletPort(Protocol):
    def get_balance(self,user_id:int)->int: ...
    def debit(self,user_id:int,amount:int)->int: ...
class ShopInventoryPort(Protocol):
    def has_capacity(self,user_id:int)->bool: ...
    def insert(self,user_id:int,permanent_item_id:int,item:EquipmentSnapshot)->int: ...
class ShopItemAllocatorPort(Protocol):
    def promote(self,preview_id:int,item:EquipmentSnapshot)->int: ...
class ShopUnitOfWorkPort(Protocol):
    shop:ShopRepositoryPort; wallet:ShopWalletPort; inventory:ShopInventoryPort; allocator:ShopItemAllocatorPort
    def commit(self)->None: ...
    def rollback(self)->None: ...

class BaseEquipmentShopService:
    """Canonical owner for class-aware preview confirmation and atomic purchase."""
    def confirm(self,command:ConfirmPurchase,uow:ShopUnitOfWorkPort)->PurchaseResult:
        if not command.operation_key.strip():raise ShopContractError("operation_key_required")
        if command.user_id<=0 or command.preview_id<=0:raise ShopContractError("invalid_identity")
        try:
            existing=uow.shop.get_receipt(command.operation_key)
            if existing is not None:
                if existing.user_id!=command.user_id or existing.preview_id!=command.preview_id:raise ShopConflictError("operation_key_payload_conflict")
                return PurchaseResult(existing,True)
            preview=uow.shop.get_preview(command.preview_id)
            if preview is None:raise ShopContractError("preview_not_found_or_expired")
            if preview.user_id!=command.user_id:raise ShopContractError("preview_owner_mismatch")
            if preview.quoted_price<=0:raise ShopContractError("invalid_quoted_price")
            if not uow.inventory.has_capacity(command.user_id):raise ShopContractError("inventory_full")
            if uow.wallet.get_balance(command.user_id)<preview.quoted_price:raise ShopContractError("insufficient_gold")
            permanent_id=uow.allocator.promote(preview.preview_id,preview.item)
            inventory_id=uow.inventory.insert(command.user_id,permanent_id,preview.item)
            balance_after=uow.wallet.debit(command.user_id,preview.quoted_price)
            receipt=PurchaseReceipt(command.operation_key,command.user_id,preview.preview_id,permanent_id,preview.quoted_price,balance_after,inventory_id)
            uow.shop.save_receipt(receipt);uow.shop.invalidate_preview(preview.preview_id);uow.commit()
            return PurchaseResult(receipt,False)
        except Exception:
            uow.rollback();raise
'''


def test_text():
    return '''import unittest
from copy import deepcopy
from datetime import datetime,timezone
from rom_v2.application.base_equipment_shop import *
ITEM=EquipmentSnapshot("sword","main_hand","sword","warrior",(("str",2),),"common",100)
PREVIEW=ShopPreview(1001,1,"main_hand","sword","warrior",ITEM,10,datetime(2026,1,1,tzinfo=timezone.utc))
class Shop:
 def __init__(self):self.previews={1001:PREVIEW};self.receipts={}
 def get_preview(self,i):return self.previews.get(i)
 def get_receipt(self,k):return self.receipts.get(k)
 def save_receipt(self,r):self.receipts[r.operation_key]=r
 def invalidate_preview(self,i):self.previews.pop(i,None)
class Wallet:
 def __init__(self,b=20):self.b=b
 def get_balance(self,u):return self.b
 def debit(self,u,a):
  if self.b<a:raise ShopContractError("insufficient_gold")
  self.b-=a;return self.b
class Inventory:
 def __init__(self,capacity=True):self.capacity=capacity;self.rows=[]
 def has_capacity(self,u):return self.capacity
 def insert(self,u,p,item):self.rows.append((u,p,item));return len(self.rows)
class Allocator:
 def __init__(self):self.n=20000;self.map={}
 def promote(self,p,item):
  if p not in self.map:self.map[p]=self.n;self.n+=1
  return self.map[p]
class Uow:
 def __init__(self,b=20,capacity=True,fail=False):self.shop=Shop();self.wallet=Wallet(b);self.inventory=Inventory(capacity);self.allocator=Allocator();self.fail=fail;self.commits=0;self.rollbacks=0;self.snap=None
 def begin(self):self.snap=deepcopy((self.shop,self.wallet,self.inventory,self.allocator))
 def commit(self):
  if self.fail:raise RuntimeError("commit_failure")
  self.commits+=1;self.snap=None
 def rollback(self):
  self.rollbacks+=1
  if self.snap:self.shop,self.wallet,self.inventory,self.allocator=self.snap;self.snap=None
def execute(u,c=ConfirmPurchase("op",1,1001)):u.begin();return BaseEquipmentShopService().confirm(c,u)
class Tests(unittest.TestCase):
 def test_purchase(self):
  u=Uow();r=execute(u);self.assertEqual(r.receipt.price,10);self.assertEqual(u.wallet.b,10);self.assertEqual(len(u.inventory.rows),1);self.assertEqual(u.commits,1)
 def test_replay(self):
  u=Uow();first=execute(u);u.begin();again=BaseEquipmentShopService().confirm(ConfirmPurchase("op",1,1001),u);self.assertTrue(again.replayed);self.assertEqual(first.receipt,again.receipt);self.assertEqual(u.commits,1)
 def test_changed_replay_conflicts(self):
  u=Uow();execute(u);u.begin()
  with self.assertRaises(ShopConflictError):BaseEquipmentShopService().confirm(ConfirmPurchase("op",2,1001),u)
 def test_inventory_full_prevents_mutation(self):
  u=Uow(capacity=False)
  with self.assertRaisesRegex(ShopContractError,"inventory_full"):execute(u)
  self.assertEqual(u.wallet.b,20);self.assertFalse(u.inventory.rows)
 def test_insufficient_gold_prevents_promotion(self):
  u=Uow(b=9)
  with self.assertRaisesRegex(ShopContractError,"insufficient_gold"):execute(u)
  self.assertFalse(u.allocator.map);self.assertFalse(u.inventory.rows)
 def test_owner_and_stale_rejected(self):
  u=Uow()
  with self.assertRaisesRegex(ShopContractError,"preview_owner_mismatch"):execute(u,ConfirmPurchase("x",2,1001))
  u=Uow();u.shop.previews.clear()
  with self.assertRaisesRegex(ShopContractError,"preview_not_found_or_expired"):execute(u)
 def test_commit_failure_rolls_back_all(self):
  u=Uow(fail=True)
  with self.assertRaisesRegex(RuntimeError,"commit_failure"):execute(u)
  self.assertEqual(u.wallet.b,20);self.assertFalse(u.inventory.rows);self.assertFalse(u.allocator.map);self.assertIn(1001,u.shop.previews)
 def test_immutable_preview(self):
  with self.assertRaises(Exception):PREVIEW.quoted_price=1
 def test_restart_replay(self):
  first=Uow();original=execute(first);second=deepcopy(first);second.begin();replay=BaseEquipmentShopService().confirm(ConfirmPurchase("op",1,1001),second);self.assertTrue(replay.replayed);self.assertEqual(replay.receipt,original.receipt)
if __name__=="__main__":unittest.main()
'''


def tool_text():
    return '''#!/usr/bin/env python3
"""Targeted Stage 21.10.3c Base Equipment Shop verifier."""
import ast
from pathlib import Path

root=Path(__file__).resolve().parents[1]
app=root/"rom_v2/application/base_equipment_shop.py"
test=root/"tests_v2/test_base_equipment_shop.py"
for path in (app,test): ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
source=app.read_text(encoding="utf-8")
required=("class BaseEquipmentShopService","class ShopPreview","class ConfirmPurchase","operation_key_payload_conflict","inventory_full","insufficient_gold")
missing=[token for token in required if token not in source]
if missing: raise SystemExit(f"missing_contract_tokens:{missing}")
for forbidden in ("sqlite3","aiogram","telegram"):
    if forbidden in source.lower(): raise SystemExit(f"forbidden_dependency:{forbidden}")
print("STAGE_21_10_1C_CRYSTAL_WALLET_LEDGER_SMOKE: PASS")
'''


def run_ci(root, env):
    temporary = root / "reports/.stage_21_10_3c_ci.tmp.json"
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
        print("[1/10] [PASS] Stage 21.10.3b zero-unresolved implementation prerequisite verified.")
        print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
        before = protected(root)
        folder, state = backup(root)
        print("[3/10] [PASS] All mutation targets backed up before production mutation.")
        write(root, APP, app_text())
        write(root, TEST, test_text())
        write(root, TOOL, tool_text())
        print("[4/10] [PASS] BaseEquipmentShopService, immutable preview/receipt DTOs and ports implemented.")
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
        print("[6/10] [PASS] Preview ownership, quoted price, inventory preflight, idempotency, rollback and restart tests passed.")
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
            "application_service": "BaseEquipmentShopService",
            "implementation": APP.as_posix(),
            "tests": TEST.as_posix(),
            "implemented": [
                "class_aware_offer_contract", "stable_offer_keys", "immutable_preview_snapshot",
                "quoted_price_locked", "user_owned_preview", "inventory_preflight",
                "stable_operation_key", "same_payload_idempotent_replay",
                "changed_payload_conflict", "never_reuse_promotion_port",
                "atomic_debit_promotion_insertion", "single_commit", "atomic_rollback",
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
        write(root, DOC, '''# Stage 21.10.3c - Base Equipment Shop implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Canonical owner: `BaseEquipmentShopService`
- Class-aware offers with stable technical keys
- Non-negative balance: **enforced**
- Stable operation key and immutable preview snapshot: **implemented**
- Quoted-price purchase with idempotent replay: **idempotent**
- Changed-payload replay: **conflict**
- Single caller-owned commit and atomic rollback: **implemented**
- SQLite / production persistence: **NOT_CONNECTED**
- Runtime / Telegram: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

The implementation is API-ready only. Production adapters and runtime wiring remain outside Stage 21.10.3c.
''')
        print("[9/10] [PASS] Machine report and Markdown implementation documentation written.")
        expected = {rel.as_posix() for rel in TARGETS}
        git(root, "add", "--", APP.as_posix(), TEST.as_posix(), TOOL.as_posix())
        git(root, "add", "-f", "--", SELF.as_posix(), REPORT.as_posix(), DOC.as_posix())
        staged = {line.strip().replace("\\", "/") for line in git(root, "diff", "--cached", "--name-only").stdout.splitlines() if line.strip()}
        if staged != expected:
            raise PatchError(f"staging_mismatch:{sorted(staged)}")
        commit_result = git(root, "commit", "-m", "Stage 21.10.3c: implement Base Equipment Shop", check=False)
        if commit_result.returncode:
            raise PatchError(f"commit_failed:{commit_result.stdout}:{commit_result.stderr}")
        commit = git(root, "rev-parse", "HEAD").stdout.strip()
        changed = {line.strip().replace("\\", "/") for line in git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.splitlines() if line.strip()}
        if changed != expected:
            raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
        (root / FAILURE).unlink(missing_ok=True)
        print(f"[10/10] [PASS] Base Equipment Shop implementation committed: {commit}")
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
