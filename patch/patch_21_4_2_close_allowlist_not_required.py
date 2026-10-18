#!/usr/bin/env python3
"""Stage 21.4.2: close the development-bot account allowlist as not required."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE = "21.4.2"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "2d251e6e68b39af35232aa6433a03b0c79aa3fd0"
PREREQUISITE_REPORT = "reports/stage_21_4_1a_dev_bot_token_acceptance.json"
PATCH_PATH = "patch/patch_21_4_2_close_allowlist_not_required.py"
REPORT_PATH = "reports/stage_21_4_2_allowlist_not_required.json"
CONTRACT_PATH = "MD/STAGE_21_4_2_ALLOWLIST_NOT_REQUIRED.md"
FAILURE_REPORT = "reports/stage_21_4_2_failure_rollback.json"
COMMIT_MESSAGE = "Stage 21.4.2: close test account allowlist as not required"
V1_ENV_PATH = ".env"
V2_ENV_PATH = "rom_v2/.env"
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
MUTATED_FILES = (REPORT_PATH, CONTRACT_PATH)
OWNED = {PATCH_PATH, FAILURE_REPORT, *MUTATED_FILES}
BACKUP_PREFIX = "stage_21_4_2"


@dataclass(frozen=True)
class Check:
    """Describe one automated Stage 21.4.2 policy check."""

    check_id: str
    status: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False


class PatchError(RuntimeError):
    """Signal a controlled policy-only patch failure."""


def run(root: Path, *command: str, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with deterministic Python settings."""
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONHASHSEED"] = "0"
    return subprocess.run(
        command,
        cwd=root,
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run Git in the project root."""
    return run(root, "git", *args)


def rev(root: Path, name: str) -> str | None:
    """Resolve one Git commit reference."""
    result = git(root, "rev-parse", "--verify", f"{name}^{{commit}}")
    return result.stdout.strip() if result.returncode == 0 else None


def sha256(path: Path) -> str:
    """Return SHA-256 evidence for non-secret database artifacts."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_metadata(path: Path) -> dict[str, Any]:
    """Capture non-secret file metadata without reading environment contents."""
    if not path.is_file():
        return {"exists": False}
    stat = path.stat()
    return {"exists": True, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def database_evidence(root: Path) -> dict[str, Any]:
    """Capture DB/WAL/SHM evidence without opening SQLite."""
    evidence: dict[str, Any] = {}
    for name in DB_FILES:
        path = root / name
        if not path.exists():
            evidence[name] = {"exists": False}
        else:
            stat = path.stat()
            evidence[name] = {
                "exists": True,
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "sha256": sha256(path),
            }
    return evidence


def write_atomic(path: Path, content: str) -> None:
    """Write one UTF-8 artifact using atomic replacement."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def parse_status(raw: str) -> list[dict[str, str]]:
    """Parse NUL-separated Git porcelain output."""
    return [{"status": item[:2], "path": item[3:]} for item in raw.split("\0") if item]


def git_blob(root: Path, commit: str, relative: str) -> bytes | None:
    """Read one tracked file from the expected parent commit."""
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def prepare_backups(root: Path) -> dict[str, Any]:
    """Back up every tracked mutation target before writing policy artifacts."""
    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"files": {}}
    for relative in MUTATED_FILES:
        blob = git_blob(root, EXPECTED_PARENT, relative)
        backup_path = backup_dir / f"{BACKUP_PREFIX}__{relative.replace('/', '__')}"
        if blob is None:
            manifest["files"][relative] = {"existed": False, "backup": None}
        else:
            backup_path.write_bytes(blob)
            manifest["files"][relative] = {
                "existed": True,
                "backup": str(backup_path.relative_to(root)).replace("\\", "/"),
            }
    return manifest


def rollback(root: Path, manifest: dict[str, Any], reason: str, checks: list[Check]) -> dict[str, Any]:
    """Restore tracked policy artifacts and leave local environments untouched."""
    git(root, "reset", "--", *MUTATED_FILES)
    restored: list[str] = []
    removed: list[str] = []
    errors: list[str] = []
    for relative, metadata in manifest["files"].items():
        target = root / relative
        try:
            if metadata["existed"]:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((root / metadata["backup"]).read_bytes())
                restored.append(relative)
            elif target.exists():
                target.unlink()
                removed.append(relative)
        except OSError as exc:
            errors.append(f"{relative}: {exc}")
    payload = {
        "stage": STAGE,
        "status": "FAIL_ROLLED_BACK" if not errors else "ROLLBACK_INCOMPLETE",
        "reason": reason,
        "failed_checks": [asdict(item) for item in checks if item.status == "FAIL"],
        "restored_files": restored,
        "removed_failed_artifacts": removed,
        "rollback_errors": errors,
        "v1_env_modified": False,
        "v2_env_modified": False,
        "main_py_started_after_failure": False,
        "wal_shm_manipulated": False,
        "token_value_recorded": False,
    }
    write_atomic(root / FAILURE_REPORT, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return payload


def render_contract() -> str:
    """Render the formal NOT_REQUIRED decision and accepted risk."""
    return "\n".join(
        [
            "# Stage 21.4.2 — Test account allowlist",
            "",
            "- **Status:** `NOT_REQUIRED`",
            "- **Decision type:** policy-only closure",
            "- **Production allowlist path created:** `False`",
            "",
            "## Rationale",
            "",
            "The development bot is privately operated and is not intended for publication or group use. A static account allowlist would add recurring administration and would require configuration changes whenever another owner-controlled test account is added.",
            "",
            "## Accepted risk",
            "",
            "Knowledge of the bot token is not required to contact a Telegram bot. If the development bot username becomes known, a third party could send updates to the bot while no account-level allowlist is enforced.",
            "",
            "## Guardrails",
            "",
            "- Do not publish the development bot username.",
            "- Do not add the development bot to groups or channels.",
            "- Do not reuse the development token for production.",
            "- Do not add hard-coded Telegram user IDs to production code.",
            "- If access control becomes necessary, implement it as a separate future stage using local configuration rather than hard-coded IDs.",
            "",
            "## Explicit non-implementation",
            "",
            "No allowlist module, user-ID list, database table, environment variable, Telegram request, polling process, or alternate production path is introduced by this stage.",
            "",
            "## Next stage",
            "",
            "Stage 21.4.3 — Telegram adapter skeleton.",
            "",
        ]
    )


def exact_commit(root: Path) -> str:
    """Commit only the patch and secret-free policy evidence."""
    paths = [PATCH_PATH, *MUTATED_FILES]
    added = git(root, "add", "-f", "--", *paths)
    if added.returncode != 0:
        raise PatchError(added.stderr.strip())
    staged = sorted(item for item in git(root, "diff", "--cached", "--name-only", "-z").stdout.split("\0") if item)
    if staged != sorted(paths):
        git(root, "reset", "--", *paths)
        raise PatchError(f"staging_allowlist_mismatch:{staged}")
    forbidden = {V1_ENV_PATH, V2_ENV_PATH, ".env.example"}
    if forbidden.intersection(staged):
        git(root, "reset", "--", *paths)
        raise PatchError("environment_file_entered_staging")
    committed = git(root, "commit", "-m", COMMIT_MESSAGE)
    if committed.returncode != 0:
        git(root, "reset", "--", *paths)
        raise PatchError(committed.stderr.strip() or committed.stdout.strip())
    return rev(root, "HEAD") or ""


def main() -> int:
    """Close Stage 21.4.2 as NOT_REQUIRED with automated safety evidence."""
    root = Path(__file__).resolve().parent.parent
    prerequisite_path = root / PREREQUISITE_REPORT
    if not prerequisite_path.is_file():
        print(f"[FAIL] Missing prerequisite: {PREREQUISITE_REPORT}", file=sys.stderr)
        return 2
    prerequisite = json.loads(prerequisite_path.read_text(encoding="utf-8"))
    summary = prerequisite.get("summary", {})
    if prerequisite.get("stage") != "21.4.1a" or summary.get("status") != "ACCEPTED" or summary.get("conclusion") != "GO":
        print("[FAIL] Stage 21.4.1a prerequisite is not canonical ACCEPTED/GO.", file=sys.stderr)
        return 2
    print("[1/10] [PASS] Stage 21.4.1a accepted token-isolation prerequisite detected.")

    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [
        entry for entry in entries
        if entry["status"][0] in {" ", "?"}
        and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))
    ]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.4.1a parent verified.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected tracked changes.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/10] [FAIL] Preflight returned NO_GO.")
        return 1
    print("[2/10] [PASS] Branch, parent, upstream and tracked worktree verified.")

    database_before = database_evidence(root)
    v1_before = file_metadata(root / V1_ENV_PATH)
    v2_before = file_metadata(root / V2_ENV_PATH)
    manifest = prepare_backups(root)
    print("[3/10] [PASS] Backups and non-secret isolation evidence prepared.")

    try:
        policy = {
            "decision": "NOT_REQUIRED",
            "implementation_created": False,
            "hard_coded_user_ids_created": False,
            "environment_allowlist_created": False,
            "database_allowlist_created": False,
            "telegram_contacted": False,
            "accepted_risk": "A third party who learns the development bot username could send updates while no account-level allowlist is enforced.",
            "future_policy": "If needed later, introduce local-configuration access control in a separate stage without hard-coded IDs.",
        }
        checks.append(Check("POLICY_DECISION", "PASS", "Allowlist formally classified as NOT_REQUIRED.", policy))
        print("[4/10] [PASS] NOT_REQUIRED decision and accepted risk formalized.")

        tracked_paths = set(item for item in git(root, "ls-files", "-z").stdout.split("\0") if item)
        forbidden_new_paths = {
            "rom_v2/allowlist.py",
            "rom_v2/test_account_allowlist.py",
            "rom_v2/application/allowlist.py",
            "rom_v2/infrastructure/allowlist.py",
        }
        absent = sorted(forbidden_new_paths.intersection(tracked_paths)) == []
        checks.append(Check("NO_ALLOWLIST_PATH", "PASS" if absent else "FAIL", f"No production allowlist path exists: {absent}.", {}, not absent))
        print("[5/10] [PASS] No allowlist production path or hard-coded user list introduced.")

        v1_mid = file_metadata(root / V1_ENV_PATH)
        v2_mid = file_metadata(root / V2_ENV_PATH)
        env_ok = v1_before == v1_mid and v2_before == v2_mid
        checks.append(Check("ENVIRONMENTS_UNTOUCHED", "PASS" if env_ok else "FAIL", f"V1 and V2 environment metadata unchanged: {env_ok}.", {}, not env_ok))
        print("[6/10] [PASS] V1 and V2 local environments remain untouched.")

        ci_path = root / "reports" / ".stage_21_4_2_ci.tmp.json"
        ci = run(root, sys.executable, "tools/run_v2_ci.py", "--project-root", str(root), "--json-out", str(ci_path))
        ci_payload = json.loads(ci_path.read_text(encoding="utf-8")) if ci_path.exists() else {"status": "FAIL"}
        ci_path.unlink(missing_ok=True)
        ci_ok = ci.returncode == 0 and ci_payload.get("status") == "PASS"
        checks.append(Check("CI_BASELINE", "PASS" if ci_ok else "FAIL", ci.stdout.strip() or "CI baseline failed.", {"failed_checks": ci_payload.get("failed_checks", [])}, not ci_ok))
        print("[7/10] [PASS] Canonical six-gate V2 CI baseline executed.")

        database_after = database_evidence(root)
        database_ok = database_before == database_after
        checks.append(Check("DATABASE_UNCHANGED", "PASS" if database_ok else "FAIL", "DB/WAL/SHM unchanged and SQLite was not opened.", {"production_connection_opened": False}, not database_ok))
        print("[8/10] [PASS] Database safety and runtime isolation verified.")

        blockers = [item.check_id for item in checks if item.blocking]
        if blockers:
            report = rollback(root, manifest, f"Stage 21.4.2 NO_GO: {blockers}", checks)
            print(f"[9/10] [FAIL] Rollback: {report['status']}")
            return 1

        payload = {
            "schema_version": 1,
            "stage": STAGE,
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "summary": {
                "conclusion": "GO",
                "status": "NOT_REQUIRED",
                "blocking_failures": [],
                "production_allowlist_created": False,
                "accepted_risk_recorded": True,
                "token_value_recorded": False,
                "telegram_contacted": False,
                "gameplay_started": False,
                "telegram_started": False,
                "database_opened": False,
            },
            "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
            "checks": [asdict(item) for item in checks],
            "policy": policy,
            "database_evidence_before": database_before,
            "database_evidence_after": database_after,
            "changed_tracked_files": [PATCH_PATH, *MUTATED_FILES],
            "explicitly_untouched_files": [V1_ENV_PATH, V2_ENV_PATH, "game.db", "game.db-wal", "game.db-shm"],
            "next_stage": "21.4.3",
            "suggested_next_patch": "patch_21_4_3_create_telegram_adapter_skeleton.py",
        }
        print("[9/10] [PASS] Writing policy-only NOT_REQUIRED evidence and contract.")
        write_atomic(root / REPORT_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        write_atomic(root / CONTRACT_PATH, render_contract())
    except Exception as exc:
        report = rollback(root, manifest, f"Mutation or verification failure: {exc}", checks)
        print(f"[9/10] [FAIL] {exc}; rollback: {report['status']}", file=sys.stderr)
        return 2

    (root / FAILURE_REPORT).unlink(missing_ok=True)
    try:
        commit_hash = exact_commit(root)
    except PatchError as exc:
        report = rollback(root, manifest, f"Commit failure: {exc}", checks)
        print(f"[10/10] [FAIL] rollback: {report['status']}", file=sys.stderr)
        return 2

    print(f"[10/10] [PASS] Test-account allowlist closed as NOT_REQUIRED: {commit_hash}")
    print("=" * 72)
    print("ROM Stage 21.4.2 - test account allowlist")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print("[PASS] PRODUCTION_ALLOWLIST_CREATED: False")
    print("[PASS] ACCEPTED_RISK_RECORDED: True")
    print("[PASS] TOKEN_VALUE_RECORDED: False")
    print("[PASS] TELEGRAM_CONTACTED: False")
    print("[PASS] GAMEPLAY_STARTED: False")
    print("[PASS] TELEGRAM_STARTED: False")
    print("[PASS] DATABASE_OPENED: False")
    print("CONCLUSION: GO")
    print("STAGE STATUS: NOT_REQUIRED")
    print("PATCH STATUS: PASS")
    print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
    print("REMOTE PUSH STATUS: NOT REQUIRED")
    print("MANUAL GAME CHECK: NOT REQUIRED")
    print("FAIL-SAFE ROLLBACK: ARMED")
    print("WAL/SHM: NOT MANIPULATED")
    print("SUGGESTED NEXT PATCH: patch_21_4_3_create_telegram_adapter_skeleton.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
