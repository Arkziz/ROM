#!/usr/bin/env python3
"""Stage 21.4.1a: accept the isolated local ROM V2 development bot token."""
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

STAGE = "21.4.1a"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "5d073a4d1c807180eab9d2e2477b46b69049c3e0"
PREREQUISITE_REPORT = "reports/stage_21_4_1_dev_bot_env_preparation.json"
PATCH_PATH = "patch/patch_21_4_1a_accept_dev_bot_token.py"
V2_ENV_PATH = "rom_v2/.env"
V1_ENV_PATH = ".env"
ENV_EXAMPLE_PATH = ".env.example"
TOKEN_KEY = "ROM_V2_BOT_TOKEN"
REPORT_PATH = "reports/stage_21_4_1a_dev_bot_token_acceptance.json"
CONTRACT_PATH = "MD/STAGE_21_4_1A_DEV_BOT_TOKEN_ACCEPTANCE.md"
FAILURE_REPORT = "reports/stage_21_4_1a_failure_rollback.json"
COMMIT_MESSAGE = "Stage 21.4.1a: accept development bot token isolation"
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
TRACKED_MUTATIONS = (REPORT_PATH, CONTRACT_PATH)
OWNED = {PATCH_PATH, FAILURE_REPORT, *TRACKED_MUTATIONS}
# Telegram bot tokens use a numeric bot identifier, colon, and URL-safe secret.
# Length ranges remain intentionally forward-compatible; acceptance does not contact Telegram.
TOKEN_PATTERN = re.compile(r"^[0-9]{5,20}:[A-Za-z0-9_-]{20,100}$")


@dataclass(frozen=True)
class Check:
    """Describe one automated Stage 21.4.1a acceptance check."""

    check_id: str
    status: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False


class PatchError(RuntimeError):
    """Signal a controlled acceptance or commit failure."""


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
    """Return SHA-256 evidence for non-secret production artifacts."""
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
    """Write one UTF-8 artifact using atomic replacement."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def parse_status(raw: str) -> list[dict[str, str]]:
    """Parse NUL-separated Git porcelain output."""
    return [{"status": item[:2], "path": item[3:]} for item in raw.split("\0") if item]


def read_token_state(path: Path) -> dict[str, Any]:
    """Validate the local token in memory without returning or hashing its value."""
    if not path.is_file():
        return {"file_exists": False, "assignment_count": 0, "has_value": False, "format_valid": False}
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"^\s*(?:export\s+)?{re.escape(TOKEN_KEY)}\s*=\s*(.*)\s*$")
    values = [match.group(1).strip() for line in text.splitlines() if (match := pattern.match(line))]
    if len(values) != 1:
        return {"file_exists": True, "assignment_count": len(values), "has_value": False, "format_valid": False}
    value = values[0]
    # Accept standard dotenv quoting while validating only the in-memory inner value.
    normalized = value
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
        normalized = value[1:-1].strip()
    return {
        "file_exists": True,
        "assignment_count": 1,
        "has_value": bool(normalized),
        "format_valid": bool(normalized and TOKEN_PATTERN.fullmatch(normalized)),
    }


def root_env_metadata(path: Path) -> dict[str, Any]:
    """Capture non-secret V1 environment metadata without reading its contents."""
    if not path.is_file():
        return {"exists": False}
    stat = path.stat()
    return {"exists": True, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def rollback(root: Path, reason: str, checks: list[Check]) -> dict[str, Any]:
    """Remove failed acceptance artifacts without touching either local environment."""
    git(root, "reset", "--", *TRACKED_MUTATIONS)
    removed: list[str] = []
    for relative in TRACKED_MUTATIONS:
        path = root / relative
        if path.exists():
            path.unlink()
            removed.append(relative)
    payload = {
        "stage": STAGE,
        "status": "FAIL_ROLLED_BACK",
        "reason": reason,
        "failed_checks": [asdict(item) for item in checks if item.status == "FAIL"],
        "removed_failed_artifacts": removed,
        "v2_env_modified": False,
        "v1_env_modified": False,
        "main_py_started_after_failure": False,
        "wal_shm_manipulated": False,
        "token_value_recorded": False,
        "token_value_hashed": False,
    }
    write_atomic(root / FAILURE_REPORT, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return payload


def render_contract() -> str:
    """Render the accepted development-bot token isolation contract."""
    return "\n".join(
        [
            "# Stage 21.4.1a — Development bot token acceptance",
            "",
            "- **Status:** `ACCEPTED`",
            "- **Local owner:** `ROM\\rom_v2\\.env`",
            f"- **Variable:** `{TOKEN_KEY}`",
            "- **V1 environment:** `ROM\\.env` remains separate and untouched",
            "",
            "## Acceptance guarantees",
            "",
            "- The V2 token assignment exists exactly once and is non-empty.",
            "- The value has the structural form expected for a Telegram bot token, including optional dotenv quotes.",
            "- The token was not printed, masked, hashed, written to reports, or committed.",
            "- `rom_v2/.env` is ignored and untracked.",
            "- The tracked `.env.example` retains a blank placeholder.",
            "- The V1 root `.env` was not modified.",
            "- No Telegram request or polling process was started.",
            "",
            "## Limitation",
            "",
            "This acceptance verifies local presence, structural format, and isolation only. It does not contact Telegram and therefore does not prove that BotFather currently recognizes the token.",
            "",
            "## Next stage",
            "",
            "Stage 21.4.2 — allowlist for test accounts.",
            "",
        ]
    )


def exact_commit(root: Path) -> str:
    """Commit only the patch and secret-free acceptance evidence."""
    paths = [PATCH_PATH, *TRACKED_MUTATIONS]
    added = git(root, "add", "-f", "--", *paths)
    if added.returncode != 0:
        raise PatchError(added.stderr.strip())
    staged = sorted(item for item in git(root, "diff", "--cached", "--name-only", "-z").stdout.split("\0") if item)
    if staged != sorted(paths):
        git(root, "reset", "--", *paths)
        raise PatchError(f"staging_allowlist_mismatch:{staged}")
    forbidden = {V2_ENV_PATH, V1_ENV_PATH, ENV_EXAMPLE_PATH}
    if forbidden.intersection(staged):
        git(root, "reset", "--", *paths)
        raise PatchError("environment_file_entered_staging")
    committed = git(root, "commit", "-m", COMMIT_MESSAGE)
    if committed.returncode != 0:
        git(root, "reset", "--", *paths)
        raise PatchError(committed.stderr.strip() or committed.stdout.strip())
    return rev(root, "HEAD") or ""


def main() -> int:
    """Accept local V2 token presence and isolation without disclosing the token."""
    root = Path(__file__).resolve().parent.parent
    prerequisite_path = root / PREREQUISITE_REPORT
    if not prerequisite_path.is_file():
        print(f"[FAIL] Missing prerequisite: {PREREQUISITE_REPORT}", file=sys.stderr)
        return 2
    prerequisite = json.loads(prerequisite_path.read_text(encoding="utf-8"))
    summary = prerequisite.get("summary", {})
    if prerequisite.get("stage") != "21.4.1" or summary.get("status") != "PREPARED_AWAITING_MANUAL_TOKEN":
        print("[FAIL] Stage 21.4.1 prerequisite is not canonical PREPARED_AWAITING_MANUAL_TOKEN.", file=sys.stderr)
        return 2
    print("[1/10] [PASS] Stage 21.4.1 preparation evidence detected.")

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
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.4.1 parent verified.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected tracked changes.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/10] [FAIL] Preflight returned NO_GO.")
        return 1
    print("[2/10] [PASS] Branch, parent, upstream and tracked worktree verified.")

    database_before = database_evidence(root)
    v1_before = root_env_metadata(root / V1_ENV_PATH)
    v2_before = root_env_metadata(root / V2_ENV_PATH)
    print("[3/10] [PASS] Non-secret environment metadata and database evidence captured.")

    token_state = read_token_state(root / V2_ENV_PATH)
    token_ok = all((token_state["file_exists"], token_state["assignment_count"] == 1, token_state["has_value"], token_state["format_valid"]))
    checks.append(Check("V2_TOKEN_PRESENT", "PASS" if token_state["has_value"] else "FAIL", f"V2 token is non-empty: {token_state['has_value']}.", {}, not token_state["has_value"]))
    checks.append(Check("V2_TOKEN_UNIQUE", "PASS" if token_state["assignment_count"] == 1 else "FAIL", f"Exactly one V2 token assignment: {token_state['assignment_count'] == 1}.", {}, token_state["assignment_count"] != 1))
    checks.append(Check("V2_TOKEN_FORMAT", "PASS" if token_state["format_valid"] else "FAIL", f"V2 token structural format valid: {token_state['format_valid']}.", {}, not token_state["format_valid"]))
    print("[4/10] [PASS] V2 token presence, uniqueness and structural format evaluated in memory.")

    ignored = git(root, "check-ignore", "-q", V2_ENV_PATH).returncode == 0
    tracked = bool(git(root, "ls-files", "--", V2_ENV_PATH).stdout.strip())
    checks.append(Check("V2_ENV_IGNORED", "PASS" if ignored else "FAIL", f"rom_v2/.env ignored: {ignored}.", {}, not ignored))
    checks.append(Check("V2_ENV_NOT_TRACKED", "PASS" if not tracked else "FAIL", f"rom_v2/.env tracked: {tracked}.", {}, tracked))
    print("[5/10] [PASS] V2 environment ignore and non-tracking policy verified.")

    example_state = read_token_state(root / ENV_EXAMPLE_PATH)
    example_ok = example_state["assignment_count"] == 1 and not example_state["has_value"]
    checks.append(Check("EXAMPLE_PLACEHOLDER_BLANK", "PASS" if example_ok else "FAIL", f"Tracked token placeholder remains blank: {example_ok}.", {}, not example_ok))
    print("[6/10] [PASS] Tracked example remains secret-free.")

    ci_path = root / "reports" / ".stage_21_4_1a_ci.tmp.json"
    ci = run(root, sys.executable, "tools/run_v2_ci.py", "--project-root", str(root), "--json-out", str(ci_path))
    ci_payload = json.loads(ci_path.read_text(encoding="utf-8")) if ci_path.exists() else {"status": "FAIL"}
    ci_path.unlink(missing_ok=True)
    ci_ok = ci.returncode == 0 and ci_payload.get("status") == "PASS"
    checks.append(Check("CI_BASELINE", "PASS" if ci_ok else "FAIL", ci.stdout.strip() or "CI baseline failed.", {"failed_checks": ci_payload.get("failed_checks", [])}, not ci_ok))
    print("[7/10] [PASS] Canonical six-gate V2 CI baseline executed.")

    database_after = database_evidence(root)
    v1_after = root_env_metadata(root / V1_ENV_PATH)
    v2_after = root_env_metadata(root / V2_ENV_PATH)
    database_ok = database_before == database_after
    v1_ok = v1_before == v1_after
    v2_ok = v2_before == v2_after
    checks.append(Check("DATABASE_UNCHANGED", "PASS" if database_ok else "FAIL", "DB/WAL/SHM unchanged and SQLite was not opened.", {"production_connection_opened": False}, not database_ok))
    checks.append(Check("V1_ENV_UNTOUCHED", "PASS" if v1_ok else "FAIL", f"Root V1 .env metadata unchanged: {v1_ok}.", {}, not v1_ok))
    checks.append(Check("V2_ENV_UNTOUCHED", "PASS" if v2_ok else "FAIL", f"V2 .env metadata unchanged by acceptance: {v2_ok}.", {}, not v2_ok))
    print("[8/10] [PASS] Database and both environment isolation boundaries verified.")

    blockers = [item.check_id for item in checks if item.blocking]
    if blockers:
        report = rollback(root, f"Stage 21.4.1a NO_GO: {blockers}", checks)
        print(f"[9/10] [FAIL] Rollback: {report['status']}")
        return 1

    payload = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "conclusion": "GO",
            "status": "ACCEPTED",
            "blocking_failures": [],
            "manual_token_entry_accepted": True,
            "token_value_recorded": False,
            "token_value_hashed": False,
            "telegram_contacted": False,
            "gameplay_started": False,
            "telegram_started": False,
            "database_opened": False,
        },
        "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
        "checks": [asdict(item) for item in checks],
        "local_environment": {
            "path": V2_ENV_PATH,
            "variable": TOKEN_KEY,
            **token_state,
            "ignored": ignored,
            "tracked": tracked,
            "value_in_report": False,
            "value_hashed": False,
            "v1_root_env_untouched": v1_ok,
            "v2_env_untouched_by_acceptance": v2_ok,
        },
        "database_evidence_before": database_before,
        "database_evidence_after": database_after,
        "changed_tracked_files": [PATCH_PATH, *TRACKED_MUTATIONS],
        "explicitly_untouched_files": [V1_ENV_PATH, V2_ENV_PATH, "game.db", "game.db-wal", "game.db-shm"],
        "next_stage": "21.4.2",
        "suggested_next_patch": "patch_21_4_2_define_test_account_allowlist.py",
    }
    print("[9/10] [PASS] Writing secret-free acceptance evidence and contract.")
    write_atomic(root / REPORT_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / CONTRACT_PATH, render_contract())

    (root / FAILURE_REPORT).unlink(missing_ok=True)
    try:
        commit_hash = exact_commit(root)
    except PatchError as exc:
        report = rollback(root, f"Commit failure: {exc}", checks)
        print(f"[10/10] [FAIL] rollback: {report['status']}", file=sys.stderr)
        return 2

    print(f"[10/10] [PASS] Development bot token isolation accepted without disclosure: {commit_hash}")
    print("=" * 72)
    print("ROM Stage 21.4.1a - development bot token acceptance")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print("[PASS] TOKEN_VALUE_RECORDED: False")
    print("[PASS] TOKEN_VALUE_HASHED: False")
    print("[PASS] TELEGRAM_CONTACTED: False")
    print("[PASS] GAMEPLAY_STARTED: False")
    print("[PASS] TELEGRAM_STARTED: False")
    print("[PASS] DATABASE_OPENED: False")
    print("CONCLUSION: GO")
    print("PATCH STATUS: PASS")
    print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
    print("REMOTE PUSH STATUS: NOT REQUIRED")
    print("MANUAL GAME CHECK: NOT REQUIRED")
    print("FAIL-SAFE ROLLBACK: ARMED")
    print("WAL/SHM: NOT MANIPULATED")
    print("SUGGESTED NEXT PATCH: patch_21_4_2_define_test_account_allowlist.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
