#!/usr/bin/env python3
"""Stage 21.0.2: create and publish the isolated rewrite/rom-v2 branch.

Run from ROM root while local develop points to the accepted Stage 21.0.1
commit. The patch creates the branch, writes regulated audit artifacts, creates
an exact-allowlist commit, publishes the branch, and verifies its upstream.
Production code, game.db, game.db-wal and game.db-shm are not modified.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

STAGE = "21.0.2"
SOURCE_BRANCH = "develop"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "3269cffb853872d9e199f308275c71b7f91c57ea"
PATCH_PATH = "patch/patch_21_0_2_create_rewrite_branch.py"
JSON_PATH = "reports/stage_21_0_2_create_rewrite_branch.json"
MD_PATH = "MD/STAGE_21_0_2_CREATE_REWRITE_BRANCH.md"
COMMIT_MESSAGE = "Stage 21.0.2: create ROM V2 rewrite branch"
OWNED_PATHS = {PATCH_PATH, JSON_PATH, MD_PATH}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")


@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False


class PatchError(RuntimeError):
    """Expected fail-safe patch failure."""


def run(root: Path, *command: str, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def git(root: Path, *args: str, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return run(root, "git", *args, timeout=timeout)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evidence(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in DB_FILES:
        path = root / name
        if not path.exists():
            result[name] = {"exists": False}
            continue
        stat = path.stat()
        result[name] = {
            "exists": True,
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sha256": sha256(path),
        }
    return result


def rev(root: Path, name: str) -> str | None:
    result = git(root, "rev-parse", "--verify", f"{name}^{{commit}}")
    return result.stdout.strip() if result.returncode == 0 else None


def branch_exists(root: Path, ref: str) -> bool:
    return git(root, "show-ref", "--verify", "--quiet", ref).returncode == 0


def parse_status(raw: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    parts = raw.split("\0")
    index = 0
    while index < len(parts):
        item = parts[index]
        if not item:
            index += 1
            continue
        status = item[:2]
        path = item[3:]
        entry = {"status": status, "path": path}
        if status[0] in {"R", "C"} and index + 1 < len(parts):
            entry["original_path"] = parts[index + 1]
            index += 1
        items.append(entry)
        index += 1
    return items


def write_atomic(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def make_check(check_id: str, ok: bool, good: str, bad: str, details: dict[str, Any]) -> Check:
    return Check(check_id, "PASS" if ok else "FAIL", good if ok else bad, details, not ok)


def render_markdown(payload: dict[str, Any]) -> str:
    rows = [
        f"| `{item['check_id']}` | **{item['status']}** | {'так' if item['blocking'] else 'ні'} | {item['summary'].replace('|', '/')} |"
        for item in payload["checks"]
    ]
    return "\n".join([
        "# ROM Stage 21.0.2 - створення rewrite/rom-v2", "",
        f"- **Висновок preflight:** `{payload['summary']['conclusion']}`",
        f"- **Source branch:** `{SOURCE_BRANCH}`",
        f"- **Target branch:** `{TARGET_BRANCH}`",
        f"- **Parent commit:** `{EXPECTED_PARENT}`", "",
        "## Перевірки", "",
        "| ID | Статус | Blocking | Результат |",
        "|---|---:|---:|---|", *rows, "",
        "## Операційний контракт", "",
        "- Гілка створюється тільки від прийнятого commit Stage 21.0.1.",
        "- У commit Stage 21.0.2 потрапляють тільки patch, JSON і Markdown цього підетапу.",
        "- Після commit гілка публікується як `origin/rewrite/rom-v2` з upstream tracking.",
        "- Production code і SQLite-файли не змінюються.",
        "- `game.db-wal` і `game.db-shm` не видаляються, не очищуються та не використовуються для rollback.",
        "- Якщо локальна mutation завершується невдало до успішної публікації, локальна rewrite-гілка видаляється, а Git повертається на `develop`.", "",
        "## Наступний етап", "",
        "Stage 21.0.3 - фіксація baseline ROM V1.", "",
    ])


def exact_stage(root: Path, paths: Sequence[str]) -> None:
    add = git(root, "add", "-f", "--", *paths)
    if add.returncode != 0:
        raise PatchError(add.stderr.strip() or "git add failed")
    staged_result = git(root, "diff", "--cached", "--name-only", "-z")
    if staged_result.returncode != 0:
        raise PatchError(staged_result.stderr.strip() or "cannot inspect index")
    staged = sorted(item for item in staged_result.stdout.split("\0") if item)
    if staged != sorted(paths):
        git(root, "reset", "--", *paths)
        raise PatchError(f"staging allowlist mismatch: {staged}")


def rollback_local(root: Path, original_branch: str, target_created: bool) -> dict[str, Any]:
    """Rollback only local Stage 21.0.2 Git mutations."""
    actions: list[str] = []
    current = git(root, "branch", "--show-current").stdout.strip()
    if current != original_branch:
        switched = git(root, "switch", original_branch)
        actions.append(f"switch_to_{original_branch}:{switched.returncode}")
    git(root, "reset", "--", PATCH_PATH, JSON_PATH, MD_PATH)
    if target_created and branch_exists(root, f"refs/heads/{TARGET_BRANCH}"):
        deleted = git(root, "branch", "-D", TARGET_BRANCH)
        actions.append(f"delete_local_target:{deleted.returncode}")
    return {"actions": actions, "active_branch": git(root, "branch", "--show-current").stdout.strip()}


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    if not (root / ".git").exists():
        print("[FAIL] Run this file from ROM\\patch.", file=sys.stderr)
        return 2
    if not (root / "reports").is_dir() or not (root / "MD").is_dir():
        print("[FAIL] Required reports and MD directories are missing.", file=sys.stderr)
        return 2

    db_before = evidence(root)
    original_branch = git(root, "branch", "--show-current").stdout.strip()
    target_created = False
    remote_published = False

    print("[1/8] [PASS] ROM root and artifact directories detected.")
    status_result = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if status_result.returncode != 0:
        print("[FAIL] Cannot inspect working tree.", file=sys.stderr)
        return 2
    entries = parse_status(status_result.stdout)
    allowed: list[dict[str, str]] = []
    for entry in entries:
        index_status = entry["status"][0]
        path = entry["path"]
        if index_status in {" ", "?"} and (path in OWNED_PATHS or (path in ALLOWED_DIRTY and index_status == " ")):
            allowed.append(entry)
    unexpected = [entry for entry in entries if entry not in allowed]

    print("[2/8] [PASS] Validating exact Stage 21.0.1 parent and branch preconditions.")
    source_head = rev(root, "HEAD")
    local_target = branch_exists(root, f"refs/heads/{TARGET_BRANCH}")
    cached_remote_target = branch_exists(root, f"refs/remotes/origin/{TARGET_BRANCH}")
    checks = [
        make_check("SOURCE_BRANCH", original_branch == SOURCE_BRANCH, f"Current branch is {SOURCE_BRANCH}.", f"Expected {SOURCE_BRANCH}; detected {original_branch or 'detached HEAD'}.", {"actual": original_branch}),
        make_check("EXPECTED_PARENT", source_head == EXPECTED_PARENT, "HEAD matches accepted Stage 21.0.1 commit.", "HEAD does not match accepted Stage 21.0.1 commit.", {"expected": EXPECTED_PARENT, "actual": source_head}),
        make_check("WORKTREE", not unexpected, "Working tree has no unexpected or pre-staged changes.", "Unexpected or pre-staged changes exist.", {"unexpected": unexpected, "allowed": allowed}),
        make_check("LOCAL_TARGET_ABSENT", not local_target, "Local rewrite branch does not exist.", "Local rewrite branch already exists.", {"exists": local_target}),
        make_check("CACHED_REMOTE_TARGET_ABSENT", not cached_remote_target, "Cached origin rewrite branch does not exist.", "Cached origin rewrite branch already exists.", {"exists": cached_remote_target}),
        make_check("ORIGIN_CONFIGURED", git(root, "remote", "get-url", "origin").returncode == 0, "origin remote is configured.", "origin remote is missing.", {}),
    ]
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"

    print("[3/8] [PASS] Writing regulated Stage 21.0.2 preflight artifacts.")
    payload = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {"conclusion": conclusion, "blocking_failures": blockers},
        "source": {"branch": original_branch, "head": source_head},
        "target": {"branch": TARGET_BRANCH, "local_exists_before": local_target, "cached_origin_exists_before": cached_remote_target},
        "checks": [asdict(item) for item in checks],
        "database_evidence_before": db_before,
        "artifact_policy": {"patch": PATCH_PATH, "json": JSON_PATH, "markdown": MD_PATH},
        "next_stage": "21.0.3" if conclusion == "GO" else None,
    }
    write_atomic(root / JSON_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / MD_PATH, render_markdown(payload))

    if conclusion != "GO":
        print("[4/8] [FAIL] Preconditions returned NO_GO; no branch or commit was created.")
        print("PATCH STATUS: FAIL\nGIT COMMIT STATUS: NOT CREATED\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED")
        print("Blocking failures: " + ", ".join(blockers))
        return 1

    try:
        print(f"[4/8] [PASS] Creating local branch {TARGET_BRANCH}.")
        created = git(root, "switch", "-c", TARGET_BRANCH, EXPECTED_PARENT)
        if created.returncode != 0:
            raise PatchError(created.stderr.strip() or created.stdout.strip() or "branch creation failed")
        target_created = True

        print("[5/8] [PASS] Staging exact Stage 21.0.2 allowlist.")
        exact_stage(root, [PATCH_PATH, JSON_PATH, MD_PATH])

        print("[6/8] [PASS] Creating Stage 21.0.2 commit in rewrite branch.")
        committed = git(root, "commit", "-m", COMMIT_MESSAGE)
        if committed.returncode != 0:
            raise PatchError(committed.stderr.strip() or committed.stdout.strip() or "git commit failed")
        commit_hash = rev(root, "HEAD")
        if not commit_hash:
            raise PatchError("commit created but HEAD cannot be resolved")

        print(f"[7/8] [PASS] Publishing {TARGET_BRANCH} and configuring upstream.")
        pushed = git(root, "push", "-u", "origin", TARGET_BRANCH, timeout=180)
        if pushed.returncode != 0:
            raise PatchError(pushed.stderr.strip() or pushed.stdout.strip() or "git push failed")
        remote_published = True

        remote_hash = rev(root, f"origin/{TARGET_BRANCH}")
        upstream = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        db_after = evidence(root)
        final_ok = (
            git(root, "branch", "--show-current").stdout.strip() == TARGET_BRANCH
            and remote_hash == commit_hash
            and upstream.returncode == 0
            and upstream.stdout.strip() == f"origin/{TARGET_BRANCH}"
            and db_before == db_after
        )
        if not final_ok:
            raise PatchError("final branch/upstream/DB consistency verification failed")

        print("[8/8] [PASS] Local branch, remote branch, upstream and DB evidence verified.")
        print("=" * 72)
        print(f"ROM Stage {STAGE} - create rewrite branch")
        print("=" * 72)
        for item in checks:
            print(f"[{item.status}] {item.check_id}: {item.summary}")
        print(f"[PASS] TARGET_BRANCH: {TARGET_BRANCH}")
        print(f"[PASS] LOCAL_COMMIT: {commit_hash}")
        print(f"[PASS] REMOTE_COMMIT: {remote_hash}")
        print(f"[PASS] UPSTREAM: {upstream.stdout.strip()}")
        print("-" * 72)
        print("CONCLUSION: GO")
        print("PATCH STATUS: PASS")
        print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
        print("REMOTE PUSH STATUS: PASS")
        print("MANUAL CHECK: NOT REQUIRED")
        print("WAL/SHM: NOT MANIPULATED")
        return 0
    except (PatchError, subprocess.TimeoutExpired) as exc:
        # A remote branch cannot be silently deleted after publication. If push
        # succeeded but final verification failed, stop fail-closed and retain it
        # for explicit recovery. Before publication, local mutations are rolled back.
        if not remote_published:
            recovery = rollback_local(root, original_branch, target_created)
            recovery_text = json.dumps(recovery, ensure_ascii=False)
        else:
            recovery_text = "remote already published; explicit recovery required"
        print(f"[FAIL] {exc}", file=sys.stderr)
        print(f"RECOVERY: {recovery_text}")
        print("PATCH STATUS: FAIL")
        print("GIT COMMIT STATUS: FAILED OR RECOVERY REQUIRED")
        print("MANUAL CHECK: NOT REQUIRED")
        print("WAL/SHM: NOT MANIPULATED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
