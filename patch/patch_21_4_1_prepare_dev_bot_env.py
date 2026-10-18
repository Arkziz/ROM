#!/usr/bin/env python3
"""Stage 21.4.1: prepare the isolated ignored ROM V2 environment for a development bot token."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE = "21.4.1"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "88f37efe3a6e41b6ff61acb00ff84f922b52d313"
PREREQUISITE_REPORT = "reports/stage_21_3_6_ci_baseline.json"
PATCH_PATH = "patch/patch_21_4_1_prepare_dev_bot_env.py"
LOCAL_ENV_PATH = "rom_v2/.env"
ENV_EXAMPLE_PATH = ".env.example"
V1_ENV_PATH = ".env"
REPORT_PATH = "reports/stage_21_4_1_dev_bot_env_preparation.json"
CONTRACT_PATH = "MD/STAGE_21_4_1_DEV_BOT_ENV_PREPARATION.md"
FAILURE_REPORT = "reports/stage_21_4_1_failure_rollback.json"
COMMIT_MESSAGE = "Stage 21.4.1: prepare development bot environment"
TOKEN_KEY = "ROM_V2_BOT_TOKEN"
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
TRACKED_MUTATIONS = (REPORT_PATH, CONTRACT_PATH)
OWNED = {PATCH_PATH, FAILURE_REPORT, *TRACKED_MUTATIONS}
BACKUP_NAME = "backup/stage_21_4_1__rom_v2__env"


@dataclass(frozen=True)
class Check:
    """Describe one automated Stage 21.4.1 preparation check."""

    check_id: str
    status: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False


class PatchError(RuntimeError):
    """Signal a controlled patch failure."""


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
    """Return SHA-256 evidence without interpreting file contents."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    """Write one UTF-8 file using atomic replacement."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def parse_status(raw: str) -> list[dict[str, str]]:
    """Parse NUL-separated Git porcelain output."""
    return [{"status": item[:2], "path": item[3:]} for item in raw.split("\0") if item]


def token_assignments(text: str) -> list[str]:
    """Return token assignment values without logging or persisting them."""
    values: list[str] = []
    pattern = re.compile(rf"^\s*(?:export\s+)?{re.escape(TOKEN_KEY)}\s*=\s*(.*)\s*$")
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            values.append(match.group(1).strip())
    return values


def prepare_local_env(root: Path) -> dict[str, Any]:
    """Create or extend rom_v2/.env without overwriting any token value."""
    env_path = root / LOCAL_ENV_PATH
    existed = env_path.exists()
    original = env_path.read_text(encoding="utf-8") if existed else ""
    assignments = token_assignments(original)
    if len(assignments) > 1:
        raise PatchError(f"duplicate_{TOKEN_KEY}_assignments")
    if assignments:
        return {
            "env_existed_before": existed,
            "env_created": False,
            "token_key_added": False,
            "token_has_value": bool(assignments[0]),
        }
    separator = "" if not original or original.endswith("\n") else "\n"
    block = (
        "# ROM V2 development Telegram bot (Stage 21.4.1)\n"
        "# Paste the BotFather token after the equals sign. Never commit this file.\n"
        f"{TOKEN_KEY}=\n"
    )
    write_atomic(env_path, original + separator + block)
    return {
        "env_existed_before": existed,
        "env_created": not existed,
        "token_key_added": True,
        "token_has_value": False,
    }


def backup_local_env(root: Path) -> dict[str, Any]:
    """Back up an existing rom_v2/.env before mutation without reading it into reports."""
    source = root / LOCAL_ENV_PATH
    backup = root / BACKUP_NAME
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        return {"existed": False, "backup_created": False}
    backup.write_bytes(source.read_bytes())
    return {"existed": True, "backup_created": True}


def restore_local_env(root: Path, backup: dict[str, Any]) -> dict[str, Any]:
    """Restore the prior rom_v2/.env or remove a newly created one."""
    env_path = root / LOCAL_ENV_PATH
    backup_path = root / BACKUP_NAME
    if backup["existed"]:
        env_path.write_bytes(backup_path.read_bytes())
        return {"local_env_restored": True, "new_local_env_removed": False}
    env_path.unlink(missing_ok=True)
    return {"local_env_restored": False, "new_local_env_removed": True}


def rollback(
    root: Path,
    backup: dict[str, Any],
    reason: str,
    checks: list[Check],
    database_before: dict[str, Any],
) -> dict[str, Any]:
    """Restore the isolated V2 environment and remove failed tracked artifacts."""
    git(root, "reset", "--", *TRACKED_MUTATIONS)
    for relative in TRACKED_MUTATIONS:
        (root / relative).unlink(missing_ok=True)
    recovery = restore_local_env(root, backup)
    database_after = database_evidence(root)
    payload = {
        "stage": STAGE,
        "status": "FAIL_ROLLED_BACK",
        "reason": reason,
        "failed_checks": [asdict(item) for item in checks if item.status == "FAIL"],
        **recovery,
        "database_restored": database_before == database_after,
        "database_evidence_after_rollback": database_after,
        "main_py_started_after_failure": False,
        "wal_shm_manipulated": False,
        "secret_value_recorded": False,
    }
    write_atomic(root / FAILURE_REPORT, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return payload


def render_contract(preparation: dict[str, Any]) -> str:
    """Render the human-readable preparation and manual-action contract."""
    return "\n".join(
        [
            "# Stage 21.4.1 — Development bot isolated V2 environment preparation",
            "",
            "- **Status:** `PREPARED_AWAITING_MANUAL_TOKEN`",
            "- **Local file:** `ROM\\rom_v2\\.env`",
            f"- **Variable:** `{TOKEN_KEY}`",
            "- **Git policy:** `.env` is ignored and must never be committed",
            "",
            "## Manual action",
            "",
            "Create the separate development bot through BotFather. Paste the token only after the equals sign in the isolated `rom_v2/.env` file:",
            "",
            "```dotenv",
            f"{TOKEN_KEY}=PASTE_TOKEN_HERE",
            "```",
            "",
            "Do not paste the token into chat, reports, Markdown, console commands, commits, or `.env.example`.",
            "",
            "## Preparation evidence",
            "",
            f"- `rom_v2/.env` existed before patch: **{preparation['env_existed_before']}**.",
            f"- `rom_v2/.env` created by patch: **{preparation['env_created']}**.",
            f"- Token key added by patch: **{preparation['token_key_added']}**.",
            f"- Token currently populated: **{preparation['token_has_value']}**.",
            "",
            "## Follow-up",
            "",
            "After the token is entered locally, run Stage 21.4.1a acceptance. The follow-up must verify presence and isolation without printing, masking, hashing, or otherwise recording the token value.",
            "",
        ]
    )


def exact_commit(root: Path) -> str:
    """Commit only patch, secret-free report, and Markdown contract."""
    paths = [PATCH_PATH, *TRACKED_MUTATIONS]
    added = git(root, "add", "-f", "--", *paths)
    if added.returncode != 0:
        raise PatchError(added.stderr.strip())
    staged = sorted(
        item
        for item in git(root, "diff", "--cached", "--name-only", "-z").stdout.split("\0")
        if item
    )
    if staged != sorted(paths):
        git(root, "reset", "--", *paths)
        raise PatchError(f"staging_allowlist_mismatch:{staged}")
    if LOCAL_ENV_PATH in staged or ENV_EXAMPLE_PATH in staged:
        git(root, "reset", "--", *paths)
        raise PatchError("local_or_example_env_entered_staging")
    committed = git(root, "commit", "-m", COMMIT_MESSAGE)
    if committed.returncode != 0:
        git(root, "reset", "--", *paths)
        raise PatchError(committed.stderr.strip() or committed.stdout.strip())
    return rev(root, "HEAD") or ""


def main() -> int:
    """Prepare rom_v2/.env and commit only secret-free Stage 21.4.1 evidence."""
    root = Path(__file__).resolve().parent.parent
    prerequisite_path = root / PREREQUISITE_REPORT
    if not prerequisite_path.is_file():
        print(f"[FAIL] Missing prerequisite: {PREREQUISITE_REPORT}", file=sys.stderr)
        return 2
    prerequisite = json.loads(prerequisite_path.read_text(encoding="utf-8"))
    if prerequisite.get("stage") != "21.3.6" or prerequisite.get("summary", {}).get("conclusion") != "GO":
        print("[FAIL] Stage 21.3.6 prerequisite is not canonical GO.", file=sys.stderr)
        return 2
    print("[1/10] [PASS] Stage 21.3.6 prerequisite and six-gate CI baseline detected.")

    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [
        entry
        for entry in entries
        if entry["status"][0] in {" ", "?"}
        and (
            entry["path"] in OWNED
            or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " ")
        )
    ]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.3.6 parent verified.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/10] [FAIL] Preflight returned NO_GO.")
        return 1
    print("[2/10] [PASS] Branch, parent, upstream and worktree verified.")

    database_before = database_evidence(root)
    v1_env_before = sha256(root / V1_ENV_PATH) if (root / V1_ENV_PATH).is_file() else None
    backup = backup_local_env(root)
    print("[3/10] [PASS] Existing rom_v2/.env backed up when present; backup contains no report metadata.")
    try:
        preparation = prepare_local_env(root)
        print("[4/10] [PASS] rom_v2/.env prepared without overwriting an existing token value.")

        ignored = git(root, "check-ignore", "-q", LOCAL_ENV_PATH).returncode == 0
        tracked = bool(git(root, "ls-files", "--", LOCAL_ENV_PATH).stdout.strip())
        checks.append(Check("LOCAL_ENV_IGNORED", "PASS" if ignored else "FAIL", f"rom_v2/.env ignored: {ignored}.", {}, not ignored))
        checks.append(Check("LOCAL_ENV_NOT_TRACKED", "PASS" if not tracked else "FAIL", f"rom_v2/.env tracked: {tracked}.", {}, tracked))
        v1_env_after = sha256(root / V1_ENV_PATH) if (root / V1_ENV_PATH).is_file() else None
        v1_untouched = v1_env_before == v1_env_after
        checks.append(Check("V1_ENV_UNTOUCHED", "PASS" if v1_untouched else "FAIL", f"Root V1 .env unchanged: {v1_untouched}.", {}, not v1_untouched))
        print("[5/10] [PASS] rom_v2/.env ignore/non-tracking policy and V1 .env isolation verified.")

        example_path = root / ENV_EXAMPLE_PATH
        example_text = example_path.read_text(encoding="utf-8") if example_path.exists() else ""
        example_values = token_assignments(example_text)
        example_ok = len(example_values) == 1 and example_values[0] == ""
        checks.append(Check("BLANK_EXAMPLE_PLACEHOLDER", "PASS" if example_ok else "FAIL", f"Blank {TOKEN_KEY} placeholder in .env.example: {example_ok}.", {}, not example_ok))
        current_values = token_assignments((root / LOCAL_ENV_PATH).read_text(encoding="utf-8"))
        local_ok = len(current_values) == 1
        checks.append(Check("LOCAL_TOKEN_KEY_UNIQUE", "PASS" if local_ok else "FAIL", f"Exactly one local token assignment: {local_ok}.", {}, not local_ok))
        print("[6/10] [PASS] Local key uniqueness and blank tracked example verified.")

        ci_path = root / "reports" / ".stage_21_4_1_ci.tmp.json"
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
            report = rollback(root, backup, f"Stage 21.4.1 NO_GO: {blockers}", checks, database_before)
            print(f"[9/10] [FAIL] Rollback: {report['status']}")
            return 1

        payload = {
            "schema_version": 1,
            "stage": STAGE,
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "summary": {
                "conclusion": "GO_PREPARED_AWAITING_MANUAL_TOKEN",
                "status": "PREPARED_AWAITING_MANUAL_TOKEN",
                "blocking_failures": [],
                "manual_action_required": True,
                "token_value_recorded": False,
                "token_value_hashed": False,
                "gameplay_started": False,
                "telegram_started": False,
                "database_opened": False,
            },
            "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
            "checks": [asdict(item) for item in checks],
            "local_environment": {
                "path": LOCAL_ENV_PATH,
                "variable": TOKEN_KEY,
                **preparation,
                "ignored": ignored,
                "tracked": tracked,
                "value_in_report": False,
                "v1_root_env_path": V1_ENV_PATH,
                "v1_root_env_untouched": v1_untouched,
            },
            "database_evidence_before": database_before,
            "database_evidence_after": database_after,
            "changed_tracked_files": [PATCH_PATH, *TRACKED_MUTATIONS],
            "changed_untracked_local_files": [LOCAL_ENV_PATH],
            "explicitly_untouched_files": [V1_ENV_PATH],
            "next_stage": "21.4.1a",
            "suggested_next_patch": "patch_21_4_1a_accept_dev_bot_token.py",
        }
        print("[9/10] [PASS] Writing secret-free preparation evidence and manual-action contract.")
        write_atomic(root / REPORT_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        write_atomic(root / CONTRACT_PATH, render_contract(preparation))
    except Exception as exc:
        report = rollback(root, backup, f"Mutation or verification failure: {exc}", checks, database_before)
        print(f"[9/10] [FAIL] {exc}; rollback: {report['status']}", file=sys.stderr)
        return 2

    (root / FAILURE_REPORT).unlink(missing_ok=True)
    try:
        commit_hash = exact_commit(root)
    except PatchError as exc:
        report = rollback(root, backup, f"Commit failure: {exc}", checks, database_before)
        print(f"[10/10] [FAIL] rollback: {report['status']}", file=sys.stderr)
        return 2

    print(f"[10/10] [PASS] Isolated V2 development-bot environment prepared; secret-free evidence committed: {commit_hash}")
    print("=" * 72)
    print("ROM Stage 21.4.1 - isolated V2 development bot environment preparation")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] LOCAL_ENV_PATH: {root / LOCAL_ENV_PATH}")
    print(f"[PASS] TOKEN_VARIABLE: {TOKEN_KEY}")
    print("[PASS] V1_ROOT_ENV_UNTOUCHED: True")
    print(f"[PASS] TOKEN_CURRENTLY_POPULATED: {preparation['token_has_value']}")
    print("[PASS] TOKEN_VALUE_RECORDED: False")
    print("[PASS] GAMEPLAY_STARTED: False")
    print("[PASS] TELEGRAM_STARTED: False")
    print("[PASS] DATABASE_OPENED: False")
    print("CONCLUSION: GO_PREPARED_AWAITING_MANUAL_TOKEN")
    print("PATCH STATUS: PASS")
    print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
    print("REMOTE PUSH STATUS: NOT REQUIRED")
    print("MANUAL ACTION: REQUIRED - create development bot and fill ROM_V2_BOT_TOKEN in ROM\\rom_v2\\.env")
    print("MANUAL GAME CHECK: NOT REQUIRED")
    print("FAIL-SAFE ROLLBACK: ARMED")
    print("WAL/SHM: NOT MANIPULATED")
    print("SUGGESTED FOLLOW-UP PATCH: patch_21_4_1a_accept_dev_bot_token.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
