#!/usr/bin/env python3
"""ROM Stage 21.8.8a: refine the V1 battle-persistence contract.

This patch performs a read-only semantic refinement of the Stage 21.8.8
discovery report. It does not import or execute V1 modules, open SQLite, mutate
production code, connect runtime/Telegram dispatch, or claim runtime readiness.
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

STAGE = "21.8.8a"
BRANCH = "rewrite/rom-v2"
AUDIT = Path("reports/stage_21_8_8_existing_battle_persistence_audit.json")
REPORT = Path("reports/stage_21_8_8a_refined_battle_persistence_contract.json")
DOC = Path("MD/STAGE_21_8_8A_REFINED_BATTLE_PERSISTENCE_CONTRACT.md")
FAILURE = Path("reports/stage_21_8_8a_failure_rollback.json")
SELF = Path("patch/patch_21_8_8a_refine_battle_persistence_contract.py")
TARGETS = (SELF, REPORT, DOC)
ALLOWED_DIRTY = {
    "ROM_FULL_DUMP.txt",
    FAILURE.as_posix(),
    "reports/v2_ci_failure.json",
}
PROTECTED = (
    "game.db",
    "game.db-wal",
    "game.db-shm",
    ".env",
    "rom_v2/.env",
    ".runtime/v2/db/rom_v2.db",
)

# The first eight rows are directly supported by named V1 owners. The last five
# remain deliberately unresolved because discovery evidence does not prove a
# complete resumable aggregate, revision token, or shared persistence contract.
ROWS = (
    ("V1_PERSISTENCE_OWNER", "V1_CONFIRMED", "systems/pve_auto_escape_system.py", "begin_pve_encounter", "V1 persists a PvE encounter lifecycle marker."),
    ("ACTIVE_ENCOUNTER_READ", "V1_CONFIRMED", "systems/pve_auto_escape_system.py", "get_active_pve_encounter", "V1 reads the active persisted encounter marker."),
    ("TERMINAL_CLAIM", "V1_CONFIRMED", "systems/pve_auto_escape_system.py", "claim_pve_terminal", "Terminal claim is guarded by the persisted active encounter."),
    ("RESTART_RECOVERY", "V1_CONFIRMED", "systems/pve_auto_escape_system.py", "recover_pve_encounters_after_restart", "Restart recovery expires or closes persisted PvE encounter markers."),
    ("EXPIRE_ONCE", "V1_CONFIRMED", "systems/pve_auto_escape_system.py", "expire_pve_encounters_once", "Expiry uses a claim-once path rather than duplicate terminal mutation."),
    ("PVE_CONSUMER", "V1_CONFIRMED", "handlers/combat.py", "register_combat_handlers", "PvE handler consumes begin/read encounter operations."),
    ("VICTORY_TERMINAL_CONSUMER", "V1_CONFIRMED", "handlers/combat.py", "process_victory", "Victory consumes the terminal claim boundary."),
    ("PVP_TERMINAL_PERSISTENCE", "V1_CONFIRMED", "systems/pvp_completion_service.py", "", "PvP has a separate completion/persistence boundary and is not evidence of shared PvE save/resume."),
    ("FULL_BATTLE_SNAPSHOT_SAVE", "UNRESOLVED", "", "", "No authoritative V1 owner proves persistence of the complete mutable battle aggregate after every action."),
    ("RESUME_EXACT_TURN_STATE", "UNRESOLVED", "", "", "No authoritative V1 owner proves exact restart restoration of turn, cooldowns, effects and RNG position."),
    ("STALE_ACTION_REVISION_TOKEN", "UNRESOLVED", "", "", "Encounter activity and terminal claims exist, but a canonical action revision/version token is not proven."),
    ("SHARED_PVE_PVP_BOSS_REPOSITORY", "UNRESOLVED", "", "", "V1 evidence shows separate consumers; it does not prove one shared battle repository contract."),
    ("SIMULATOR_PERSISTENCE_PARITY", "UNRESOLVED", "", "", "Simulator snapshot terminology does not prove runtime battle-persistence parity."),
)


class PatchError(RuntimeError):
    """Raised when a mandatory Stage 21.8.8a gate fails."""


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with captured UTF-8 text and optional fail-closed checking."""
    cp = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if check and cp.returncode:
        raise PatchError(f"command_failed:{cmd!r}:{cp.stdout}:{cp.stderr}")
    return cp


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run Git in the repository root."""
    return run(["git", *args], root, check)


def root_from_cwd() -> Path:
    """Resolve and validate the ROM repository root without importing project code."""
    root = Path.cwd().resolve()
    if not (root / ".git").exists() or not (root / "rom_v2").is_dir():
        raise PatchError("run_from_rom_repository_root")
    return root


def sha256(path: Path) -> str | None:
    """Return a file digest, or None when the protected path is absent."""
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def protected_manifest(root: Path) -> dict[str, str | None]:
    """Capture protected runtime hashes without opening any database."""
    return {name: sha256(root / name) for name in PROTECTED}


def symbol_source(root: Path, rel: str, symbol: str) -> tuple[str, int, int, str]:
    """Return exact static source evidence for a module or named top-level symbol."""
    path = root / rel
    if not path.is_file():
        raise PatchError(f"missing_evidence_file:{rel}")
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=rel)
    if not symbol:
        return text, 1, len(text.splitlines()), sha256(path) or ""
    matches = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == symbol]
    if len(matches) != 1:
        raise PatchError(f"expected_one_symbol:{rel}:{symbol}:{len(matches)}")
    node = matches[0]
    segment = ast.get_source_segment(text, node)
    if not segment:
        raise PatchError(f"missing_symbol_source:{rel}:{symbol}")
    return segment, int(node.lineno), int(getattr(node, "end_lineno", node.lineno)), sha256(path) or ""


def preflight(root: Path) -> None:
    """Verify branch, audit prerequisite, latest audit commit scope, and dirty allowlist."""
    if git(root, "branch", "--show-current").stdout.strip() != BRANCH:
        raise PatchError("wrong_branch")
    if not AUDIT.is_file() and not (root / AUDIT).is_file():
        raise PatchError("missing_stage_21_8_8_audit")
    audit = json.loads((root / AUDIT).read_text(encoding="utf-8"))
    if audit.get("stage") != "21.8.8" or audit.get("status") != "PASS" or audit.get("conclusion") != "GO_TO_SEMANTIC_REFINEMENT":
        raise PatchError("invalid_stage_21_8_8_prerequisite")
    if audit.get("implementation_authorized") is not False:
        raise PatchError("audit_must_not_authorize_implementation")
    required = {row[0] for row in ROWS}
    discovered = {row.get("contract") for row in audit.get("contract_matrix", [])}
    audit_required = {
        "V1_PERSISTENCE_OWNER", "SAVE_RESUME", "RESTART_RECOVERY",
        "STALE_ACTION_PROTECTION", "SNAPSHOT_INTEGRITY", "TERMINAL_INTERACTION",
        "IDEMPOTENCY", "FAILURE_ATOMICITY", "REPOSITORY_UOW", "PVE_CONSUMERS",
        "PVP_PERSISTENCE", "BOSS_STORY_CONSUMERS", "SIMULATOR_BOUNDARY",
    }
    if not audit_required.issubset(discovered):
        raise PatchError(f"audit_contracts_missing:{sorted(audit_required - discovered)}")
    staged = git(root, "diff", "--cached", "--name-only").stdout.strip()
    if staged:
        raise PatchError("pre_staged_changes_forbidden")
    dirty = set()
    for line in git(root, "status", "--porcelain", "--untracked-files=all").stdout.splitlines():
        path = line[3:].strip().replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path == SELF.as_posix():
            continue
        if path not in ALLOWED_DIRTY:
            dirty.add(path)
    if dirty:
        raise PatchError(f"unexpected_dirty_scope:{sorted(dirty)}")
    print("[1/10] [PASS] Stage 21.8.8 audit prerequisite, branch and clean scope verified.")


def backup_targets(root: Path) -> tuple[Path, dict[str, bool]]:
    """Back up every mutable artifact before report/document mutation."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = root / "backup" / f"stage_21_8_8a_{stamp}"
    backup.mkdir(parents=True, exist_ok=False)
    state: dict[str, bool] = {}
    for rel in TARGETS:
        src = root / rel
        state[rel.as_posix()] = src.exists()
        if src.exists():
            dst = backup / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    print(f"[2/10] [PASS] Fail-safe backup created: {backup.relative_to(root).as_posix()}")
    return backup, state


def restore(root: Path, backup: Path, state: dict[str, bool]) -> list[str]:
    """Restore all artifacts changed by this patch and unstage patch scope."""
    git(root, "reset", "--", *[p.as_posix() for p in TARGETS], check=False)
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


def build_contract(root: Path) -> dict[str, Any]:
    """Build the source-bound semantic matrix without executing V1 code."""
    audit = json.loads((root / AUDIT).read_text(encoding="utf-8"))
    semantic_rows: list[dict[str, Any]] = []
    for key, classification, path, symbol, decision in ROWS:
        evidence: list[dict[str, Any]] = []
        if path:
            source, start, end, digest = symbol_source(root, path, symbol)
            evidence.append({
                "path": path,
                "symbol": symbol or "<module>",
                "line_start": start,
                "line_end": end,
                "sha256": digest,
                "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            })
        semantic_rows.append({
            "contract": key,
            "classification": classification,
            "decision": decision,
            "evidence": evidence,
        })
    unresolved = [r["contract"] for r in semantic_rows if r["classification"] == "UNRESOLVED"]
    return {
        "schema_version": 1,
        "stage": STAGE,
        "status": "PASS",
        "conclusion": "REVIEW_REQUIRED" if unresolved else "GO_TO_IMPLEMENTATION",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_audit": AUDIT.as_posix(),
        "source_audit_sha256": sha256(root / AUDIT),
        "source_audit_conclusion": audit.get("conclusion"),
        "semantic_rows": semantic_rows,
        "summary": {
            "semantic_rows": len(semantic_rows),
            "v1_confirmed_rows": sum(r["classification"] == "V1_CONFIRMED" for r in semantic_rows),
            "unresolved_rows": len(unresolved),
            "unresolved_contracts": unresolved,
            "database_opened": False,
            "production_code_changed": False,
            "runtime_dispatch_connected": False,
            "production_persistence_connected": False,
            "runtime_ready_claimed": False,
            "v1_wal_shm_manipulated": False,
        },
        "implementation_authorized": not unresolved,
        "manual_game_check": "NOT_REQUIRED",
        "suggested_next_patch": (
            "patch_21_8_8b_resolve_battle_persistence_parity.py"
            if unresolved else "patch_21_8_8b_implement_battle_persistence.py"
        ),
    }


def markdown(payload: dict[str, Any]) -> str:
    """Render the human-readable contract from the machine payload."""
    summary = payload["summary"]
    lines = [
        "# Stage 21.8.8a - Refined V1 battle persistence contract",
        "",
        f"- Status: **{payload['status']}**",
        f"- Conclusion: **{payload['conclusion']}**",
        f"- Semantic rows: **{summary['semantic_rows']}**",
        f"- V1-confirmed rows: **{summary['v1_confirmed_rows']}**",
        f"- Unresolved rows: **{summary['unresolved_rows']}**",
        "- Database opened: **False**",
        "- Production code changed: **False**",
        "- Runtime/Telegram dispatch connected: **False**",
        "- Production persistence connected: **False**",
        "- Manual game check: **NOT_REQUIRED**",
        "",
        "## Authority decision",
        "",
        "V1 persists a narrow PvE encounter lifecycle marker through `systems/pve_auto_escape_system.py` and consumes it from `handlers/combat.py`. This evidence supports active-encounter read, terminal claim, expiry-once and restart cleanup. It does not prove persistence and exact resumption of the complete mutable battle aggregate.",
        "",
        "PvP completion, boss/story consumers and simulator snapshots remain separate evidence boundaries. They are not treated as a shared battle repository or as proof of resumable-turn parity.",
        "",
        "## Semantic matrix",
        "",
    ]
    for row in payload["semantic_rows"]:
        lines.append(f"- `{row['contract']}`: **{row['classification']}** - {row['decision']}")
    lines += [
        "",
        "## Mutation gate",
        "",
        "Battle-persistence implementation is **not authorized** while any semantic row remains `UNRESOLVED`. The next patch must resolve only the listed parity gaps from V1 evidence or formally classify them as not implemented in V1. It must not invent full-battle save/resume, RNG restoration, action versions, shared PvE/PvP storage, or simulator persistence.",
        "",
        "Runtime/Telegram dispatch and production persistence remain unconnected. This stage does not claim `RUNTIME_READY`.",
        "",
        "## Safety",
        "",
        "V1 modules were parsed only as text/AST. SQLite was not opened. `game.db-wal` and `game.db-shm` were not deleted, cleared, modified, or used for rollback.",
        "",
        "## Manual game check",
        "",
        "`NOT_REQUIRED`. This is a read-only semantic refinement with no gameplay dispatch.",
        "",
        "## Suggested next patch",
        "",
        f"`{payload['suggested_next_patch']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    """Execute guarded refinement, exact-scope commit, and fail-safe rollback."""
    root = root_from_cwd()
    backup: Path | None = None
    state: dict[str, bool] = {}
    before = protected_manifest(root)
    try:
        preflight(root)
        backup, state = backup_targets(root)
        payload = build_contract(root)
        print("[3/10] [PASS] Named V1 owners and unresolved persistence claims classified.")
        if payload["summary"]["semantic_rows"] != len(ROWS):
            raise PatchError("semantic_row_count_mismatch")
        print("[4/10] [PASS] Complete semantic matrix built without V1 imports or execution.")
        (root / REPORT).parent.mkdir(parents=True, exist_ok=True)
        (root / DOC).parent.mkdir(parents=True, exist_ok=True)
        (root / REPORT).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (root / DOC).write_text(markdown(payload), encoding="utf-8")
        print("[5/10] [PASS] Machine JSON and Markdown contract artifacts written.")
        ast.parse((root / SELF).read_text(encoding="utf-8"), filename=SELF.as_posix())
        ast.parse((root / AUDIT).read_text(encoding="utf-8"), filename=AUDIT.as_posix()) if False else None
        json.loads((root / REPORT).read_text(encoding="utf-8"))
        print("[6/10] [PASS] Patch syntax and generated JSON validated.")
        ci = run([sys.executable, "tools/run_v2_ci.py"], root, check=False)
        if ci.returncode:
            raise PatchError(f"canonical_v2_ci_failed:{ci.stdout}:{ci.stderr}")
        print("[7/10] [PASS] Canonical six-gate V2 CI passed.")
        after = protected_manifest(root)
        if before != after:
            raise PatchError("protected_runtime_changed")
        print("[8/10] [PASS] V1 DB/WAL/SHM, secrets and V2 runtime DB are byte-unchanged.")
        expected = {p.as_posix() for p in TARGETS}
        git(root, "add", "-f", "--", *sorted(expected))
        staged = {p.strip().replace("\\", "/") for p in git(root, "diff", "--cached", "--name-only").stdout.splitlines() if p.strip()}
        if staged != expected:
            raise PatchError(f"staging_mismatch:{sorted(staged)}")
        print("[9/10] [PASS] Exact Git staging allowlist verified.")
        cp = git(root, "commit", "-m", "Stage 21.8.8a: refine battle persistence contract", check=False)
        if cp.returncode:
            raise PatchError(f"commit_failed:{cp.stdout}:{cp.stderr}")
        commit = git(root, "rev-parse", "HEAD").stdout.strip()
        changed = {p.strip().replace("\\", "/") for p in git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.splitlines() if p.strip()}
        if changed != expected:
            raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
        (root / FAILURE).unlink(missing_ok=True)
        print(f"[10/10] [PASS] Battle persistence semantic refinement committed: {commit}")
        print(f"CONCLUSION: {payload['conclusion']}")
        print(f"UNRESOLVED_CONTRACTS: {payload['summary']['unresolved_rows']}")
        print("IMPLEMENTATION AUTHORIZED: False")
        print("RUNTIME_READY: False")
        print("MANUAL GAME CHECK: NOT_REQUIRED")
        print("FAIL-SAFE ROLLBACK: ARMED")
        print(f"SUGGESTED NEXT PATCH: {payload['suggested_next_patch']}")
        return 0
    except Exception as exc:
        restored: list[str] = []
        if backup is not None:
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
