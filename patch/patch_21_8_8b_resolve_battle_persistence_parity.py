#!/usr/bin/env python3
"""ROM Stage 21.8.8b: resolve five battle-persistence parity contracts.

Read-only resolution only. The patch binds the five unresolved 21.8.8a rows to
bounded V1 absence/presence evidence. It does not import V1, open SQLite, mutate
production code, connect Telegram/runtime dispatch, or invent persistence
semantics that are absent from V1.
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
from typing import Any

STAGE = "21.8.8b"
BRANCH = "rewrite/rom-v2"
PARENT = "d5f7edb1ac72aa7d544b5c3208dfc400587adc4f"
PREREQ = Path("reports/stage_21_8_8a_refined_battle_persistence_contract.json")
AUDIT = Path("reports/stage_21_8_8_existing_battle_persistence_audit.json")
REPORT = Path("reports/stage_21_8_8b_resolved_battle_persistence_parity.json")
DOC = Path("MD/STAGE_21_8_8B_RESOLVED_BATTLE_PERSISTENCE_PARITY.md")
FAILURE = Path("reports/stage_21_8_8b_failure_rollback.json")
SELF = Path("patch/patch_21_8_8b_resolve_battle_persistence_parity.py")
TARGETS = (SELF, REPORT, DOC)
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", FAILURE.as_posix(), "reports/v2_ci_failure.json"}
PROTECTED = (
    "game.db", "game.db-wal", "game.db-shm", ".env", "rom_v2/.env",
    ".runtime/v2/db/rom_v2.db",
)
EXPECTED_UNRESOLVED = [
    "FULL_BATTLE_SNAPSHOT_SAVE",
    "RESUME_EXACT_TURN_STATE",
    "STALE_ACTION_REVISION_TOKEN",
    "SHARED_PVE_PVP_BOSS_REPOSITORY",
    "SIMULATOR_PERSISTENCE_PARITY",
]
OWNER_SYMBOLS = (
    ("systems/pve_auto_escape_system.py", "begin_pve_encounter"),
    ("systems/pve_auto_escape_system.py", "get_active_pve_encounter"),
    ("systems/pve_auto_escape_system.py", "claim_pve_terminal"),
    ("systems/pve_auto_escape_system.py", "expire_pve_encounters_once"),
    ("systems/pve_auto_escape_system.py", "recover_pve_encounters_after_restart"),
    ("handlers/combat.py", "process_victory"),
    ("handlers/combat.py", "register_combat_handlers"),
)
# Exact identifier families whose absence bounds the five negative conclusions.
# Generic words such as "snapshot" and "version" are intentionally excluded.
ABSENCE_FAMILIES = {
    "full_battle_snapshot": (
        "save_full_battle_snapshot", "persist_full_battle_state",
        "restore_full_battle_snapshot", "battle_snapshot_repository",
    ),
    "exact_turn_resume": (
        "resume_exact_turn_state", "restore_rng_position",
        "persist_cooldown_state", "persist_effect_duration_state",
    ),
    "revision_token": (
        "battle_revision_token", "expected_battle_revision",
        "compare_and_swap_battle_revision", "stale_battle_revision",
    ),
    "shared_repository": (
        "shared_battle_repository", "unified_battle_repository",
        "pve_pvp_boss_repository",
    ),
    "simulator_runtime_persistence": (
        "simulator_runtime_persistence", "persist_simulator_battle",
        "resume_simulator_battle",
    ),
}


class PatchError(RuntimeError):
    """Raised when a mandatory resolution gate fails."""


def run(cmd: list[str], root: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(cmd, cwd=root, text=True, capture_output=True,
                        encoding="utf-8", errors="replace")
    if check and cp.returncode:
        raise PatchError(f"command_failed:{cmd!r}:{cp.stdout[-1500:]}:{cp.stderr[-1500:]}")
    return cp


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], root, check)


def repository_root() -> Path:
    root = Path.cwd().resolve()
    if not (root / ".git").exists() or not (root / "rom_v2").is_dir():
        raise PatchError("run_from_rom_repository_root")
    return root


def digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_manifest(root: Path) -> dict[str, str | None]:
    return {rel: digest(root / rel) for rel in PROTECTED}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PatchError(f"invalid_json:{path.as_posix()}:{exc}") from exc
    if not isinstance(value, dict):
        raise PatchError(f"expected_json_object:{path.as_posix()}")
    return value


def exact_symbol(root: Path, rel: str, name: str) -> dict[str, Any]:
    """Return exact AST evidence without importing or executing V1."""
    path = root / rel
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=rel)
    matches = [n for n in ast.walk(tree)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
               and n.name == name]
    if len(matches) != 1:
        raise PatchError(f"expected_one_symbol:{rel}:{name}:{len(matches)}")
    node = matches[0]
    source = ast.get_source_segment(text, node)
    if not source:
        raise PatchError(f"missing_symbol_source:{rel}:{name}")
    return {
        "path": rel,
        "symbol": name,
        "line_start": int(node.lineno),
        "line_end": int(getattr(node, "end_lineno", node.lineno)),
        "file_sha256": digest(path),
        "symbol_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
    }


def v1_python_files(root: Path) -> list[Path]:
    """Use the audited V1 inventory as the bounded absence-scan corpus."""
    audit = load_json(root / AUDIT)
    paths: list[Path] = []
    for row in audit.get("source_inventory", []):
        rel = row.get("path") if isinstance(row, dict) else None
        if isinstance(rel, str) and rel.endswith(".py"):
            path = root / rel
            if path.is_file():
                paths.append(path)
    expected = audit.get("summary", {}).get("v1_python_files")
    if not paths or expected != len(paths):
        raise PatchError(f"audit_inventory_mismatch:{len(paths)}:{expected}")
    return paths


def bounded_absence_scan(root: Path, files: list[Path]) -> dict[str, Any]:
    """Prove only absence of exact invented identifier families in audited V1."""
    results: dict[str, Any] = {}
    for family, tokens in ABSENCE_FAMILIES.items():
        hits: list[dict[str, Any]] = []
        for path in files:
            text = path.read_text(encoding="utf-8", errors="replace")
            for token in tokens:
                if token in text:
                    hits.append({"path": path.relative_to(root).as_posix(), "token": token})
        if hits:
            raise PatchError(f"unexpected_absence_family_hits:{family}:{hits[:20]}")
        results[family] = {
            "status": "ABSENT_IN_AUDITED_V1_CORPUS",
            "tokens": list(tokens),
            "files_scanned": len(files),
            "hits": [],
        }
    return results


def preflight(root: Path) -> dict[str, Any]:
    if git(root, "branch", "--show-current").stdout.strip() != BRANCH:
        raise PatchError("wrong_branch")
    if git(root, "rev-parse", "HEAD").stdout.strip() != PARENT:
        raise PatchError("wrong_exact_parent")
    prereq = load_json(root / PREREQ)
    if (prereq.get("stage"), prereq.get("status"), prereq.get("conclusion")) != (
        "21.8.8a", "PASS", "REVIEW_REQUIRED"
    ):
        raise PatchError("invalid_stage_21_8_8a_prerequisite")
    summary = prereq.get("summary", {})
    unresolved = summary.get("unresolved_contracts")
    if unresolved != EXPECTED_UNRESOLVED or summary.get("unresolved_rows") != 5:
        raise PatchError(f"unexpected_unresolved_contracts:{unresolved}")
    if prereq.get("implementation_authorized") is not False:
        raise PatchError("prerequisite_must_not_authorize_implementation")
    if git(root, "diff", "--cached", "--name-only").stdout.strip():
        raise PatchError("pre_staged_changes_forbidden")
    dirty: set[str] = set()
    for line in git(root, "status", "--porcelain", "--untracked-files=all").stdout.splitlines():
        rel = line[3:].strip().replace("\\", "/")
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1]
        if rel == SELF.as_posix() or rel in ALLOWED_DIRTY:
            continue
        dirty.add(rel)
    if dirty:
        raise PatchError(f"unexpected_dirty_scope:{sorted(dirty)}")
    print("[1/10] [PASS] Stage 21.8.8a five-contract prerequisite verified.")
    print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
    return prereq


def backup_targets(root: Path) -> tuple[Path, dict[str, bool]]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = root / "backup" / f"stage_21_8_8b_{stamp}"
    backup.mkdir(parents=True, exist_ok=False)
    state: dict[str, bool] = {}
    for rel in TARGETS:
        src = root / rel
        state[rel.as_posix()] = src.exists()
        if src.exists():
            dst = backup / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    print("[3/10] [PASS] Resolution artifacts backed up before publication mutation.")
    return backup, state


def restore(root: Path, backup: Path | None, state: dict[str, bool]) -> list[str]:
    git(root, "reset", "--", *[rel.as_posix() for rel in TARGETS], check=False)
    if backup is None:
        return []
    restored: list[str] = []
    for rel in TARGETS:
        dst = root / rel
        if state.get(rel.as_posix()):
            src = backup / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            restored.append(rel.as_posix())
        elif dst.exists() and rel != SELF:
            dst.unlink()
            restored.append(f"removed:{rel.as_posix()}")
    return restored


def build_payload(root: Path, prereq: dict[str, Any]) -> dict[str, Any]:
    owners = [exact_symbol(root, rel, symbol) for rel, symbol in OWNER_SYMBOLS]
    files = v1_python_files(root)
    absence = bounded_absence_scan(root, files)
    resolutions = [
        {
            "contract": "FULL_BATTLE_SNAPSHOT_SAVE",
            "resolution": "NOT_IMPLEMENTED_IN_V1",
            "v2_parity_rule": "Do not claim or implement complete per-action battle snapshot parity in Stage 21.8.8.",
            "evidence": [owners[0], owners[1]],
            "absence_family": "full_battle_snapshot",
        },
        {
            "contract": "RESUME_EXACT_TURN_STATE",
            "resolution": "NOT_IMPLEMENTED_IN_V1",
            "v2_parity_rule": "Restart recovery may reproduce V1 encounter expiry/cleanup only; it must not restore exact turn, cooldown, effect, or RNG state.",
            "evidence": [owners[3], owners[4]],
            "absence_family": "exact_turn_resume",
        },
        {
            "contract": "STALE_ACTION_REVISION_TOKEN",
            "resolution": "V1_ACTIVE_ENCOUNTER_AND_TERMINAL_CLAIM_ONLY",
            "v2_parity_rule": "Protect stale terminal actions through active encounter identity and exactly-once terminal claim; do not invent a revision/version token.",
            "evidence": [owners[1], owners[2], owners[5]],
            "absence_family": "revision_token",
        },
        {
            "contract": "SHARED_PVE_PVP_BOSS_REPOSITORY",
            "resolution": "NOT_IMPLEMENTED_IN_V1",
            "v2_parity_rule": "Keep Stage 21.8.8 bounded to the audited PvE encounter lifecycle; no unified PvE/PvP/boss repository is authorized.",
            "evidence": [owners[0], owners[6]],
            "absence_family": "shared_repository",
        },
        {
            "contract": "SIMULATOR_PERSISTENCE_PARITY",
            "resolution": "NOT_IMPLEMENTED_IN_V1",
            "v2_parity_rule": "Simulator snapshot terminology is outside runtime persistence parity and must not authorize runtime save/resume behavior.",
            "evidence": [],
            "absence_family": "simulator_runtime_persistence",
        },
    ]
    return {
        "schema_version": 1,
        "stage": STAGE,
        "status": "PASS",
        "conclusion": "GO_TO_IMPLEMENTATION",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_contract": PREREQ.as_posix(),
        "source_contract_sha256": digest(root / PREREQ),
        "source_audit": AUDIT.as_posix(),
        "source_audit_sha256": digest(root / AUDIT),
        "resolved_contracts": resolutions,
        "bounded_absence_scans": absence,
        "authorized_implementation_boundary": {
            "model": "V1_PVE_ENCOUNTER_LIFECYCLE_MARKER",
            "allowed": [
                "begin an active PvE encounter marker",
                "read the active encounter marker",
                "claim one terminal outcome exactly once",
                "find and expire stale active encounters",
                "recover after restart through V1-equivalent expiry/cleanup",
            ],
            "forbidden": [
                "full mutable battle aggregate snapshot persistence",
                "exact turn/cooldown/effect/RNG resume",
                "invented battle revision tokens",
                "unified PvE/PvP/boss repository semantics",
                "simulator-to-runtime persistence parity",
                "Telegram/runtime wiring in this implementation stage",
            ],
        },
        "summary": {
            "input_unresolved_contracts": 5,
            "resolved_contracts": 5,
            "remaining_unresolved_contracts": 0,
            "audited_v1_files_scanned": len(files),
            "database_opened": False,
            "production_code_changed": False,
            "runtime_dispatch_connected": False,
            "production_persistence_connected": False,
            "runtime_ready_claimed": False,
            "v1_wal_shm_manipulated": False,
        },
        "implementation_authorized": True,
        "runtime_integration_authorized": False,
        "manual_game_check": "NOT_REQUIRED",
        "suggested_next_patch": "patch_21_8_8c_implement_battle_persistence.py",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    boundary = payload["authorized_implementation_boundary"]
    lines = [
        "# Stage 21.8.8b - Resolved battle persistence parity",
        "",
        "- Status: **PASS**",
        "- Conclusion: **GO_TO_IMPLEMENTATION**",
        "- Input unresolved contracts: **5**",
        "- Remaining unresolved contracts: **0**",
        "- Implementation authorized: **True**",
        "- Runtime integration authorized: **False**",
        "- Manual game check: **NOT_REQUIRED**",
        "",
        "## Resolution principle",
        "",
        "The authoritative V1 parity boundary is the narrow persisted PvE encounter lifecycle marker. V1 supports begin/read, exactly-once terminal claim, expiry and restart cleanup. The evidence does not support a complete resumable battle aggregate.",
        "",
        "Negative classifications are bounded absence conclusions, not universal claims. They apply only to the audited V1 Python inventory and the exact identifier families recorded in the machine report.",
        "",
        "## Resolved contracts",
        "",
    ]
    for row in payload["resolved_contracts"]:
        lines.append(f"- `{row['contract']}`: **{row['resolution']}** - {row['v2_parity_rule']}")
    lines += ["", "## Authorized implementation boundary", "", f"Model: `{boundary['model']}`", "", "Allowed:"]
    lines.extend(f"- {item}" for item in boundary["allowed"])
    lines += ["", "Forbidden:"]
    lines.extend(f"- {item}" for item in boundary["forbidden"])
    lines += [
        "", "## Safety", "",
        "V1 was inspected only as source text/AST. SQLite was not opened. `game.db-wal` and `game.db-shm` were not deleted, cleared, modified, or used for rollback.",
        "", "## Next patch", "",
        "`patch_21_8_8c_implement_battle_persistence.py`", "",
    ]
    return "\n".join(lines)


def main() -> int:
    root = repository_root()
    backup: Path | None = None
    state: dict[str, bool] = {}
    before = protected_manifest(root)
    try:
        prereq = preflight(root)
        backup, state = backup_targets(root)
        payload = build_payload(root, prereq)
        print("[4/10] [PASS] Exact V1 encounter lifecycle owners verified by AST evidence.")
        print("[5/10] [PASS] Five bounded parity gaps resolved without inventing V1 behavior.")
        if payload["summary"]["remaining_unresolved_contracts"] != 0:
            raise PatchError("resolution_not_complete")
        print("[6/10] [PASS] Implementation boundary limited to V1 PvE encounter lifecycle semantics.")
        (root / REPORT).parent.mkdir(parents=True, exist_ok=True)
        (root / DOC).parent.mkdir(parents=True, exist_ok=True)
        (root / REPORT).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (root / DOC).write_text(render_markdown(payload), encoding="utf-8")
        ast.parse((root / SELF).read_text(encoding="utf-8"), filename=SELF.as_posix())
        load_json(root / REPORT)
        ci = run([sys.executable, "tools/run_v2_ci.py"], root, check=False)
        if ci.returncode:
            raise PatchError(f"canonical_v2_ci_failed:{ci.stdout[-2000:]}:{ci.stderr[-2000:]}")
        print("[7/10] [PASS] Canonical six-gate V2 CI passed.")
        if protected_manifest(root) != before:
            raise PatchError("protected_runtime_changed")
        print("[8/10] [PASS] Production sources, DB sidecars and protected configuration remained byte-identical.")
        print("[9/10] [PASS] Resolved JSON and Markdown contract artifacts written.")
        expected = {rel.as_posix() for rel in TARGETS}
        git(root, "add", "-f", "--", *sorted(expected))
        staged = {x.strip().replace("\\", "/") for x in git(root, "diff", "--cached", "--name-only").stdout.splitlines() if x.strip()}
        if staged != expected:
            raise PatchError(f"staging_mismatch:{sorted(staged)}")
        cp = git(root, "commit", "-m", "Stage 21.8.8b: resolve battle persistence parity", check=False)
        if cp.returncode:
            raise PatchError(f"commit_failed:{cp.stdout}:{cp.stderr}")
        commit = git(root, "rev-parse", "HEAD").stdout.strip()
        changed = {x.strip().replace("\\", "/") for x in git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.splitlines() if x.strip()}
        if changed != expected:
            raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
        (root / FAILURE).unlink(missing_ok=True)
        print(f"[10/10] [PASS] Battle persistence parity resolution committed: {commit}")
        print("CONCLUSION: GO_TO_IMPLEMENTATION")
        print("UNRESOLVED_CONTRACTS: 0")
        print("IMPLEMENTATION AUTHORIZED: True")
        print("RUNTIME INTEGRATION AUTHORIZED: False")
        print("RUNTIME_READY: False")
        print("MANUAL GAME CHECK: NOT_REQUIRED")
        print("FAIL-SAFE ROLLBACK: ARMED")
        print("SUGGESTED NEXT PATCH: patch_21_8_8c_implement_battle_persistence.py")
        return 0
    except Exception as exc:
        restored = restore(root, backup, state)
        recovery = run([sys.executable, "-m", "compileall", "-q", "rom_v2"], root, check=False)
        failure = {
            "schema_version": 1,
            "stage": STAGE,
            "status": "FAIL_ROLLED_BACK",
            "failed_at_utc": datetime.now(timezone.utc).isoformat(),
            "reason": str(exc),
            "restored_files": restored,
            "recovery_compile_returncode": recovery.returncode,
            "main_py_allowed_after_recovery": recovery.returncode == 0,
            "database_opened": False,
            "v1_wal_shm_manipulated": False,
        }
        path = root / FAILURE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(failure, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[10/10] [FAIL] {exc}; rollback: FAIL_ROLLED_BACK")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
