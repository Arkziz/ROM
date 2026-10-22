#!/usr/bin/env python3
"""ROM Stage 21.8.8c: implement the pure V2 battle-persistence lifecycle API.

The implementation is deliberately bounded to the V1-confirmed PvE encounter
lifecycle marker: begin, read active, exactly-once terminal claim, stale expiry,
and restart cleanup. It does not open SQLite or connect runtime/Telegram code.
"""
from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STAGE = "21.8.8c"
BRANCH = "rewrite/rom-v2"
PARENT = "4692f2a44c911ad01ddecb14b78d6e409b50e7d7"
PREREQ = Path("reports/stage_21_8_8b_resolved_battle_persistence_parity.json")
DOMAIN = Path("rom_v2/domain/battle_persistence.py")
TEST = Path("tests_v2/test_battle_persistence.py")
TOOL = Path("tools/check_stage_21_8_8c_battle_persistence.py")
REPORT = Path("reports/stage_21_8_8c_battle_persistence_implementation.json")
DOC = Path("MD/STAGE_21_8_8C_BATTLE_PERSISTENCE_IMPLEMENTATION.md")
FAILURE = Path("reports/stage_21_8_8c_failure_rollback.json")
SELF = Path("patch/patch_21_8_8c_implement_battle_persistence.py")
TARGETS = (SELF, DOMAIN, TEST, TOOL, REPORT, DOC)
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", FAILURE.as_posix(), "reports/v2_ci_failure.json"}
PROTECTED = ("game.db", "game.db-wal", "game.db-shm", ".env", "rom_v2/.env", ".runtime/v2/db/rom_v2.db")

DOMAIN_TEXT = r'''"""Pure PvE encounter lifecycle persistence contract for ROM V2.

This module models only the V1-confirmed lifecycle marker. It intentionally
contains no database, repository, Telegram, wall-clock, or full battle snapshot
logic. Callers persist returned immutable state through later application and
infrastructure stages.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable


class BattlePersistenceContractFailure(ValueError):
    """Raised when a lifecycle command violates the bounded contract."""


class PersistedEncounterStatus(str, Enum):
    ACTIVE = "active"
    VICTORY = "victory"
    DEFEAT = "defeat"
    ESCAPE = "escape"
    EXPIRED = "expired"


class PersistedEncounterTerminalOutcome(str, Enum):
    VICTORY = "victory"
    DEFEAT = "defeat"
    ESCAPE = "escape"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class PersistedEncounterMarker:
    """Immutable lifecycle marker, not a serialized mutable battle aggregate."""

    encounter_id: str
    actor_id: str
    started_at: datetime
    expires_at: datetime
    status: PersistedEncounterStatus = PersistedEncounterStatus.ACTIVE
    terminal_operation_id: str | None = None
    terminal_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.encounter_id.strip() or not self.actor_id.strip():
            raise BattlePersistenceContractFailure("encounter_id_and_actor_id_required")
        for name, value in (("started_at", self.started_at), ("expires_at", self.expires_at)):
            if value.tzinfo is None or value.utcoffset() is None:
                raise BattlePersistenceContractFailure(f"{name}_must_be_timezone_aware")
        if self.expires_at <= self.started_at:
            raise BattlePersistenceContractFailure("expires_at_must_follow_started_at")
        terminal = self.status is not PersistedEncounterStatus.ACTIVE
        if terminal != bool(self.terminal_operation_id and self.terminal_at):
            raise BattlePersistenceContractFailure("terminal_metadata_must_match_status")

    @property
    def is_active(self) -> bool:
        return self.status is PersistedEncounterStatus.ACTIVE


@dataclass(frozen=True, slots=True)
class EncounterPersistenceResult:
    marker: PersistedEncounterMarker
    accepted: bool
    duplicate: bool
    reason: str


def _aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise BattlePersistenceContractFailure(f"{name}_must_be_timezone_aware")
    return value.astimezone(timezone.utc)


def begin_persisted_encounter(encounter_id: str, actor_id: str, started_at: datetime, expires_at: datetime) -> PersistedEncounterMarker:
    """Create one active marker; repository-level actor uniqueness is deferred."""
    return PersistedEncounterMarker(encounter_id.strip(), actor_id.strip(), _aware(started_at, "started_at"), _aware(expires_at, "expires_at"))


def find_active_persisted_encounter(markers: Iterable[PersistedEncounterMarker], actor_id: str) -> PersistedEncounterMarker | None:
    """Return the sole active marker for an actor and fail closed on duplicates."""
    active = [m for m in markers if m.actor_id == actor_id and m.is_active]
    if len(active) > 1:
        raise BattlePersistenceContractFailure("multiple_active_encounters_for_actor")
    return active[0] if active else None


def claim_persisted_encounter_terminal(marker: PersistedEncounterMarker, outcome: PersistedEncounterTerminalOutcome, operation_id: str, occurred_at: datetime) -> EncounterPersistenceResult:
    """Claim one absorbing terminal outcome with operation-id idempotency."""
    operation_id = operation_id.strip()
    if not operation_id:
        raise BattlePersistenceContractFailure("operation_id_required")
    occurred = _aware(occurred_at, "occurred_at")
    if marker.is_active:
        updated = replace(marker, status=PersistedEncounterStatus(outcome.value), terminal_operation_id=operation_id, terminal_at=occurred)
        return EncounterPersistenceResult(updated, True, False, "terminal_claimed")
    duplicate = marker.terminal_operation_id == operation_id and marker.status.value == outcome.value
    return EncounterPersistenceResult(marker, False, duplicate, "duplicate_terminal_claim" if duplicate else "already_terminal")


def select_expired_persisted_encounters(markers: Iterable[PersistedEncounterMarker], now: datetime) -> tuple[PersistedEncounterMarker, ...]:
    """Select active markers whose configured expiry instant has been reached."""
    instant = _aware(now, "now")
    return tuple(sorted((m for m in markers if m.is_active and m.expires_at <= instant), key=lambda m: (m.expires_at, m.encounter_id)))


def expire_persisted_encounter_once(marker: PersistedEncounterMarker, now: datetime) -> EncounterPersistenceResult:
    """Expire an eligible marker through the same exactly-once terminal claim."""
    instant = _aware(now, "now")
    if not marker.is_active:
        return EncounterPersistenceResult(marker, False, marker.status is PersistedEncounterStatus.EXPIRED, "already_terminal")
    if marker.expires_at > instant:
        return EncounterPersistenceResult(marker, False, False, "not_expired")
    return claim_persisted_encounter_terminal(marker, PersistedEncounterTerminalOutcome.EXPIRED, f"expire:{marker.encounter_id}", instant)


def recover_persisted_encounters_after_restart(markers: Iterable[PersistedEncounterMarker], now: datetime) -> tuple[EncounterPersistenceResult, ...]:
    """Apply V1-equivalent stale expiry/cleanup, never exact battle resumption."""
    return tuple(expire_persisted_encounter_once(marker, now) for marker in select_expired_persisted_encounters(markers, now))
'''

TEST_TEXT = r'''from datetime import datetime, timedelta, timezone
import unittest

from rom_v2.domain.battle_persistence import (
    BattlePersistenceContractFailure, PersistedEncounterStatus, PersistedEncounterTerminalOutcome,
    begin_persisted_encounter, claim_persisted_encounter_terminal, expire_persisted_encounter_once, select_expired_persisted_encounters,
    find_active_persisted_encounter, recover_persisted_encounters_after_restart,
)


class BattlePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.marker = begin_persisted_encounter("e-1", "actor-1", self.t0, self.t0 + timedelta(minutes=5))

    def test_begin_and_read_active(self):
        self.assertEqual(find_active_persisted_encounter([self.marker], "actor-1"), self.marker)
        self.assertEqual(self.marker.status, PersistedEncounterStatus.ACTIVE)

    def test_terminal_claim_is_absorbing_and_idempotent(self):
        first = claim_persisted_encounter_terminal(self.marker, PersistedEncounterTerminalOutcome.VICTORY, "op-1", self.t0 + timedelta(minutes=1))
        duplicate = claim_persisted_encounter_terminal(first.marker, PersistedEncounterTerminalOutcome.VICTORY, "op-1", self.t0 + timedelta(minutes=2))
        conflict = claim_persisted_encounter_terminal(first.marker, PersistedEncounterTerminalOutcome.DEFEAT, "op-2", self.t0 + timedelta(minutes=2))
        self.assertTrue(first.accepted)
        self.assertTrue(duplicate.duplicate)
        self.assertFalse(conflict.accepted)
        self.assertEqual(conflict.marker, first.marker)

    def test_expiry_boundary_and_restart_recovery(self):
        before = expire_persisted_encounter_once(self.marker, self.t0 + timedelta(minutes=4))
        self.assertEqual(before.reason, "not_expired")
        recovered = recover_persisted_encounters_after_restart([self.marker], self.t0 + timedelta(minutes=5))
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0].marker.status, PersistedEncounterStatus.EXPIRED)
        self.assertEqual(recover_persisted_encounters_after_restart([recovered[0].marker], self.t0 + timedelta(minutes=6)), ())

    def test_expired_selection_is_deterministic(self):
        later = begin_persisted_encounter("e-2", "actor-2", self.t0, self.t0 + timedelta(minutes=4))
        found = select_expired_persisted_encounters([self.marker, later], self.t0 + timedelta(minutes=5))
        self.assertEqual([m.encounter_id for m in found], ["e-2", "e-1"])

    def test_multiple_active_for_actor_fails_closed(self):
        other = begin_persisted_encounter("e-2", "actor-1", self.t0, self.t0 + timedelta(minutes=7))
        with self.assertRaises(BattlePersistenceContractFailure):
            find_active_persisted_encounter([self.marker, other], "actor-1")

    def test_naive_time_rejected(self):
        with self.assertRaises(BattlePersistenceContractFailure):
            begin_persisted_encounter("e", "a", datetime(2026, 1, 1), self.t0 + timedelta(minutes=1))

    def test_marker_has_no_full_battle_snapshot_fields(self):
        self.assertFalse(hasattr(self.marker, "turn"))
        self.assertFalse(hasattr(self.marker, "rng_state"))
        self.assertFalse(hasattr(self.marker, "cooldowns"))
        self.assertFalse(hasattr(self.marker, "effects"))


if __name__ == "__main__":
    unittest.main()
'''

TOOL_TEXT = r'''#!/usr/bin/env python3
"""Stage 21.8.8c smoke check for the pure encounter lifecycle API."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# Direct execution sets sys.path[0] to ROM/tools, so add the repository root
# explicitly before importing rom_v2. This keeps the smoke check independent
# from the caller's PYTHONPATH while avoiding any V1/runtime import.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rom_v2.domain.battle_persistence import PersistedEncounterStatus, begin_persisted_encounter, recover_persisted_encounters_after_restart

now = datetime(2026, 1, 1, tzinfo=timezone.utc)
marker = begin_persisted_encounter("smoke-encounter", "smoke-actor", now, now + timedelta(seconds=1))
results = recover_persisted_encounters_after_restart([marker], now + timedelta(seconds=1))
assert len(results) == 1 and results[0].accepted
assert results[0].marker.status is PersistedEncounterStatus.EXPIRED
print("STAGE_21_8_8C_BATTLE_PERSISTENCE_SMOKE: PASS")
'''


class PatchError(RuntimeError):
    pass


def run(cmd, root, check=True):
    cp = subprocess.run(cmd, cwd=root, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if check and cp.returncode:
        raise PatchError(f"command_failed:{cmd!r}:{cp.stdout[-2000:]}:{cp.stderr[-2000:]}")
    return cp


def git(root, *args, check=True):
    return run(["git", *args], root, check)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def protected(root):
    return {rel: sha(root / rel) for rel in PROTECTED}


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def preflight(root):
    if git(root, "branch", "--show-current").stdout.strip() != BRANCH:
        raise PatchError("wrong_branch")
    if git(root, "rev-parse", "HEAD").stdout.strip() != PARENT:
        raise PatchError("wrong_exact_parent")
    data = json.loads((root / PREREQ).read_text(encoding="utf-8"))
    if (data.get("stage"), data.get("status"), data.get("conclusion")) != ("21.8.8b", "PASS", "GO_TO_IMPLEMENTATION"):
        raise PatchError("invalid_stage_21_8_8b_prerequisite")
    if data.get("implementation_authorized") is not True or data.get("runtime_integration_authorized") is not False:
        raise PatchError("invalid_implementation_boundary")
    if data.get("summary", {}).get("remaining_unresolved_contracts") != 0:
        raise PatchError("unresolved_contracts_remain")
    if git(root, "diff", "--cached", "--name-only").stdout.strip():
        raise PatchError("pre_staged_changes_forbidden")
    dirty = set()
    for line in git(root, "status", "--porcelain", "--untracked-files=all").stdout.splitlines():
        rel = line[3:].strip().replace("\\", "/")
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1]
        if rel == SELF.as_posix() or rel in ALLOWED_DIRTY:
            continue
        dirty.add(rel)
    if dirty:
        raise PatchError(f"unexpected_dirty_scope:{sorted(dirty)}")
    print("[1/10] [PASS] Stage 21.8.8b zero-unresolved implementation prerequisite verified.")
    print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")


def backup(root):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder = root / "backup" / f"stage_21_8_8c_{stamp}"
    folder.mkdir(parents=True, exist_ok=False)
    state = {}
    for rel in TARGETS:
        src = root / rel
        state[rel.as_posix()] = src.exists()
        if src.exists():
            dst = folder / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    print("[3/10] [PASS] Fail-safe backup created before production mutation.")
    return folder, state


def restore(root, folder, state):
    git(root, "reset", "--", *[p.as_posix() for p in TARGETS], check=False)
    restored = []
    if folder is None:
        return restored
    for rel in TARGETS:
        dst = root / rel
        if state.get(rel.as_posix()):
            src = folder / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            restored.append(rel.as_posix())
        elif dst.exists() and rel != SELF:
            dst.unlink()
            restored.append(f"removed:{rel.as_posix()}")
    return restored


def main():
    root = Path.cwd().resolve()
    if not (root / ".git").exists() or not (root / "rom_v2").is_dir():
        print("[10/10] [FAIL] run_from_rom_repository_root; rollback: NOT_STARTED")
        return 1
    folder = None
    state = {}
    before = protected(root)
    try:
        preflight(root)
        folder, state = backup(root)
        write(root, DOMAIN, DOMAIN_TEXT)
        write(root, TEST, TEST_TEXT)
        write(root, TOOL, TOOL_TEXT)
        print("[4/10] [PASS] Pure V2 PvE encounter lifecycle persistence API implemented.")
        for rel in (DOMAIN, TEST, TOOL, SELF):
            ast.parse((root / rel).read_text(encoding="utf-8"), filename=rel.as_posix())
        compile_gate = run([sys.executable, "-m", "py_compile", DOMAIN.as_posix(), TEST.as_posix(), TOOL.as_posix()], root, False)
        if compile_gate.returncode:
            raise PatchError(f"py_compile_failed:{compile_gate.stdout}:{compile_gate.stderr}")
        print("[5/10] [PASS] Python compile gate passed.")
        tests = run([sys.executable, "-m", "unittest", TEST.as_posix(), "-v"], root, False)
        if tests.returncode:
            raise PatchError(f"targeted_tests_failed:{tests.stdout}:{tests.stderr}")
        print("[6/10] [PASS] Lifecycle, idempotency, expiry, restart and boundary tests passed.")
        smoke = run([sys.executable, TOOL.as_posix()], root, False)
        if smoke.returncode or "SMOKE: PASS" not in smoke.stdout:
            raise PatchError(f"smoke_failed:{smoke.stdout}:{smoke.stderr}")
        print("[7/10] [PASS] Battle persistence smoke check passed.")
        # Earlier manual CI/import runs may leave bytecode under rom_v2/content.
        # Canonical content validation accepts source content only, so remove V2
        # cache artifacts before CI. These are generated files, not production
        # sources, persistence data, or rollback material.
        for cache in sorted((root / "rom_v2").rglob("__pycache__"), reverse=True):
            shutil.rmtree(cache, ignore_errors=True)
        for bytecode in (root / "rom_v2").rglob("*.pyc"):
            bytecode.unlink(missing_ok=True)
        ci = run([sys.executable, "tools/run_v2_ci.py"], root, False)
        if ci.returncode:
            raise PatchError(f"canonical_v2_ci_failed:{ci.stdout[-2500:]}:{ci.stderr[-2500:]}")
        if protected(root) != before:
            raise PatchError("protected_runtime_changed")
        allowed_production = {DOMAIN.as_posix()}
        production_changed = set()
        for line in git(root, "status", "--porcelain", "--untracked-files=all").stdout.splitlines():
            rel = line[3:].strip().replace("\\", "/")
            if rel.startswith("rom_v2/"):
                production_changed.add(rel)
        if production_changed != allowed_production:
            raise PatchError(f"unauthorized_production_scope:{sorted(production_changed)}")
        print("[8/10] [PASS] Canonical V2 CI passed; only authorized production module changed.")
        payload = {
            "schema_version": 1,
            "stage": STAGE,
            "status": "PASS",
            "conclusion": "API_READY",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "prerequisite": PREREQ.as_posix(),
            "implementation": DOMAIN.as_posix(),
            "tests": TEST.as_posix(),
            "smoke_tool": TOOL.as_posix(),
            "implemented_boundary": ["begin", "read_active", "claim_persisted_encounter_terminal_exactly_once", "expire_persisted_encounter_once", "restart_expiry_cleanup"],
            "not_implemented": ["full_battle_snapshot", "exact_turn_resume", "rng_resume", "revision_token", "shared_pve_pvp_boss_repository", "runtime_or_telegram_wiring"],
            "runtime_integration": "NOT_CONNECTED",
            "production_persistence": "NOT_CONNECTED",
            "manual_game_check": "NOT_REQUIRED",
            "database_opened": False,
            "v1_wal_shm_manipulated": False,
        }
        write(root, REPORT, json.dumps(payload, ensure_ascii=False, indent=2))
        write(root, DOC, """# Stage 21.8.8c - Battle persistence implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Runtime integration: **NOT_CONNECTED**
- Production persistence: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

## Implemented boundary

A pure immutable PvE encounter lifecycle API now supports begin, active-marker read, exactly-once terminal claim, deterministic stale selection, expiry-once, and restart expiry/cleanup.

This is intentionally not a full battle snapshot. It does not persist or resume turn state, cooldowns, effects, RNG position, PvP/boss aggregates, or simulator state. It has no SQLite, repository, UoW, Telegram, handler, or wall-clock dependency.

## Verification

Targeted unit tests cover absorbing terminal state, operation-id idempotency, conflicting terminal claims, expiry boundary, deterministic restart recovery, duplicate active-marker fail-closed behavior, timezone validation, and absence of full-snapshot fields. Canonical V2 CI and the dedicated smoke check pass.

## Manual check

Not required because no gameplay/runtime adapter is connected.
""")
        print("[9/10] [PASS] Machine report and Markdown documentation written.")
        expected = {p.as_posix() for p in TARGETS}
        git(root, "add", "--", DOMAIN.as_posix(), TEST.as_posix(), TOOL.as_posix())
        # patch/ and publication artifacts are intentionally ignored in this
        # repository, so force-add only those exact authorized paths.
        git(root, "add", "-f", "--", SELF.as_posix(), REPORT.as_posix(), DOC.as_posix())
        staged = {x.strip().replace("\\", "/") for x in git(root, "diff", "--cached", "--name-only").stdout.splitlines() if x.strip()}
        if staged != expected:
            raise PatchError(f"staging_mismatch:{sorted(staged)}")
        cp = git(root, "commit", "-m", "Stage 21.8.8c: implement battle persistence lifecycle", check=False)
        if cp.returncode:
            raise PatchError(f"commit_failed:{cp.stdout}:{cp.stderr}")
        commit = git(root, "rev-parse", "HEAD").stdout.strip()
        changed = {x.strip().replace("\\", "/") for x in git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.splitlines() if x.strip()}
        if changed != expected:
            raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
        (root / FAILURE).unlink(missing_ok=True)
        print(f"[10/10] [PASS] Battle persistence lifecycle implementation committed: {commit}")
        print("CONCLUSION: API_READY")
        print("PATCH STATUS: PASS")
        print(f"GIT COMMIT STATUS: PASS ({commit})")
        print("RUNTIME INTEGRATION: NOT_CONNECTED")
        print("PRODUCTION PERSISTENCE: NOT_CONNECTED")
        print("RUNTIME_READY: False")
        print("MANUAL GAME CHECK: NOT_REQUIRED")
        print("FAIL-SAFE ROLLBACK: ARMED")
        return 0
    except Exception as exc:
        restored = restore(root, folder, state)
        recovery = run([sys.executable, "-m", "compileall", "-q", "rom_v2"], root, False)
        failure = {
            "schema_version": 1, "stage": STAGE, "status": "FAIL_ROLLED_BACK",
            "failed_at_utc": datetime.now(timezone.utc).isoformat(), "reason": str(exc),
            "restored_files": restored, "recovery_compile_returncode": recovery.returncode,
            "main_py_allowed_after_recovery": recovery.returncode == 0,
            "database_opened": False, "v1_wal_shm_manipulated": False,
        }
        path = root / FAILURE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(failure, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[10/10] [FAIL] {exc}; rollback: FAIL_ROLLED_BACK")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
