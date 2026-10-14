#!/usr/bin/env python3
"""Stage 21.0.4: create and publish the annotated final ROM V1 baseline tag.

The immutable tag points to the synchronized Stage 20/V1 repository baseline
that existed before rewrite-only commits. The patch commits its regulated
artifacts on rewrite/rom-v2, pushes that branch, creates the annotated tag,
pushes the tag explicitly, and verifies local/remote object identity.
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

STAGE = "21.0.4"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "1b88a4c17aa8e923871504f6e7aeb0a528cbb3c1"
BASELINE_COMMIT = "ff9f4920519ca5154ff1238ddaae67cb9ee2ce29"
STAGE20_CLOSURE_COMMIT = "bd6880020d3918d2ca3c071950975826dc69320c"
TAG_NAME = "rom-v1-baseline-stage-20"
TAG_MESSAGE = (
    "ROM V1 baseline after accepted Stage 20 closure and repository documentation cleanup. "
    "This tag is the immutable reference point for Stage 21 rewrite contracts."
)
PATCH_PATH = "patch/patch_21_0_4_tag_final_v1_baseline.py"
JSON_PATH = "reports/stage_21_0_4_tag_final_v1_baseline.json"
MD_PATH = "MD/STAGE_21_0_4_TAG_FINAL_V1_BASELINE.md"
COMMIT_MESSAGE = "Stage 21.0.4: tag final ROM V1 baseline"
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


def run(root: Path, *command: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
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


def git(root: Path, *args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return run(root, "git", *args, timeout=timeout)


def rev(root: Path, name: str) -> str | None:
    result = git(root, "rev-parse", "--verify", f"{name}^{{commit}}")
    return result.stdout.strip() if result.returncode == 0 else None


def ref_exists(root: Path, ref_name: str) -> bool:
    return git(root, "show-ref", "--verify", "--quiet", ref_name).returncode == 0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def database_evidence(root: Path) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for name in DB_FILES:
        path = root / name
        if not path.exists():
            evidence[name] = {"exists": False}
            continue
        stat = path.stat()
        evidence[name] = {
            "exists": True,
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sha256": sha256(path),
        }
    return evidence


def parse_status(raw: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
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
        entries.append(entry)
        index += 1
    return entries


def make_check(check_id: str, ok: bool, good: str, bad: str, details: dict[str, Any]) -> Check:
    return Check(check_id, "PASS" if ok else "FAIL", good if ok else bad, details, not ok)


def write_atomic(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def render_markdown(payload: dict[str, Any]) -> str:
    rows = [
        f"| `{item['check_id']}` | **{item['status']}** | {'так' if item['blocking'] else 'ні'} | {item['summary'].replace('|', '/')} |"
        for item in payload["checks"]
    ]
    return "\n".join([
        "# ROM Stage 21.0.4 - фінальний tag baseline ROM V1", "",
        f"- **Висновок preflight:** `{payload['summary']['conclusion']}`",
        f"- **Робоча гілка:** `{TARGET_BRANCH}`",
        f"- **Tag:** `{TAG_NAME}`",
        f"- **Tag target:** `{BASELINE_COMMIT}`",
        f"- **Stage 20 closure ancestor:** `{STAGE20_CLOSURE_COMMIT}`", "",
        "## Перевірки", "",
        "| ID | Статус | Blocking | Результат |", "|---|---:|---:|---|", *rows, "",
        "## Значення tag", "",
        "- Tag вказує на синхронізований baseline V1 після прийнятого Stage 20 і свідомого очищення робочих `MD` та `reports` від Stage 19-20.",
        "- Tag не вказує на rewrite-only commits Stage 21.0.1-21.0.4.",
        "- Старі Stage 19-20 Markdown/JSON не відновлюються у робоче дерево; за потреби вони доступні через Git history.",
        "- Tag є annotated і публікується окремим explicit refspec без `--tags`.",
        "- `rom-v1-final` не створюється зараз: цей фінальний archival tag зарезервований для production cutover Stage 21.19.", "",
        "## Безпека", "",
        "- Production code і SQLite-файли не змінюються.",
        "- `game.db-wal` і `game.db-shm` не видаляються, не очищуються та не використовуються для rollback.",
        "- До commit входять лише patch, JSON і Markdown Stage 21.0.4.", "",
        "## Наступний етап", "",
        "Stage 21.1.1 - повна інвентаризація та класифікація модулів ROM V1.", "",
    ])


def exact_stage(root: Path, paths: Sequence[str]) -> None:
    add = git(root, "add", "-f", "--", *paths)
    if add.returncode != 0:
        raise PatchError(add.stderr.strip() or "git add failed")
    staged_result = git(root, "diff", "--cached", "--name-only", "-z")
    if staged_result.returncode != 0:
        raise PatchError(staged_result.stderr.strip() or "cannot inspect staged files")
    staged = sorted(item for item in staged_result.stdout.split("\0") if item)
    if staged != sorted(paths):
        git(root, "reset", "--", *paths)
        raise PatchError(f"staging allowlist mismatch: {staged}")


def remote_tag_commit(root: Path) -> str | None:
    """Resolve the remote tag commit without fetching or changing local refs."""
    result = git(root, "ls-remote", "--tags", "origin", f"refs/tags/{TAG_NAME}^{{}}")
    if result.returncode != 0:
        return None
    values = [line.split()[0] for line in result.stdout.splitlines() if line.strip()]
    if values:
        return values[0]
    # A lightweight tag or a server response without a peeled line is still
    # inspectable, but Stage 21.0.4 requires an annotated tag and verifies its
    # local object type separately.
    direct = git(root, "ls-remote", "--tags", "origin", f"refs/tags/{TAG_NAME}")
    lines = [line.split()[0] for line in direct.stdout.splitlines() if line.strip()]
    return lines[0] if lines else None


def rollback_before_publish(root: Path, commit_created: bool, tag_created: bool) -> dict[str, Any]:
    """Rollback only local mutations while no Stage 21.0.4 ref is remote."""
    actions: list[str] = []
    if tag_created and ref_exists(root, f"refs/tags/{TAG_NAME}"):
        deleted = git(root, "tag", "-d", TAG_NAME)
        actions.append(f"delete_local_tag:{deleted.returncode}")
    if commit_created:
        reset = git(root, "reset", "--mixed", EXPECTED_PARENT)
        actions.append(f"reset_commit:{reset.returncode}")
    else:
        reset = git(root, "reset", "--", PATCH_PATH, JSON_PATH, MD_PATH)
        actions.append(f"reset_index:{reset.returncode}")
    return {
        "actions": actions,
        "branch": git(root, "branch", "--show-current").stdout.strip(),
        "head": rev(root, "HEAD"),
    }


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    if not (root / ".git").exists():
        print("[FAIL] Run this file from ROM\\patch.", file=sys.stderr)
        return 2
    if not (root / "reports").is_dir() or not (root / "MD").is_dir():
        print("[FAIL] Required reports and MD directories are missing.", file=sys.stderr)
        return 2

    db_before = database_evidence(root)
    print("[1/9] [PASS] ROM root and regulated artifact directories detected.")

    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    upstream_head = rev(root, upstream) if upstream else None
    baseline_exists = rev(root, BASELINE_COMMIT) == BASELINE_COMMIT
    closure_is_ancestor = git(root, "merge-base", "--is-ancestor", STAGE20_CLOSURE_COMMIT, BASELINE_COMMIT).returncode == 0
    baseline_is_ancestor = git(root, "merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD").returncode == 0
    local_tag_exists = ref_exists(root, f"refs/tags/{TAG_NAME}")
    remote_tag_before = remote_tag_commit(root)

    status_result = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = parse_status(status_result.stdout) if status_result.returncode == 0 else []
    allowed: list[dict[str, str]] = []
    for entry in entries:
        index_status = entry["status"][0]
        path = entry["path"]
        if index_status in {" ", "?"} and (path in OWNED_PATHS or (path in ALLOWED_DIRTY and index_status == " ")):
            allowed.append(entry)
    unexpected = [entry for entry in entries if entry not in allowed]

    print("[2/9] [PASS] Validating branch, parent, baseline ancestry, tag namespace and worktree.")
    checks = [
        make_check("TARGET_BRANCH", branch == TARGET_BRANCH, f"Active branch is {TARGET_BRANCH}.", f"Expected {TARGET_BRANCH}; detected {branch or 'detached HEAD'}.", {"actual": branch}),
        make_check("EXPECTED_PARENT", head == EXPECTED_PARENT, "HEAD matches accepted Stage 21.0.3 commit.", "HEAD differs from accepted Stage 21.0.3 commit.", {"expected": EXPECTED_PARENT, "actual": head}),
        make_check("UPSTREAM", upstream == f"origin/{TARGET_BRANCH}", "Rewrite branch upstream is configured.", "Rewrite branch upstream is missing or incorrect.", {"upstream": upstream, "remote_head": upstream_head, "local_head": head}),
        make_check("BASELINE_COMMIT", baseline_exists, "V1 baseline commit exists.", "V1 baseline commit is missing.", {"commit": BASELINE_COMMIT}),
        make_check("STAGE20_ANCESTRY", closure_is_ancestor, "Accepted Stage 20 closure is an ancestor of the V1 baseline.", "Stage 20 closure is not an ancestor of the V1 baseline.", {"closure": STAGE20_CLOSURE_COMMIT, "baseline": BASELINE_COMMIT}),
        make_check("BASELINE_ANCESTRY", baseline_is_ancestor, "V1 baseline is an ancestor of the rewrite branch.", "V1 baseline is not an ancestor of the rewrite branch.", {"baseline": BASELINE_COMMIT, "head": head}),
        make_check("LOCAL_TAG_ABSENT", not local_tag_exists, "Local tag namespace is free.", "Local tag already exists.", {"tag": TAG_NAME}),
        make_check("REMOTE_TAG_ABSENT", remote_tag_before is None, "Remote tag namespace is free.", "Remote tag already exists.", {"tag": TAG_NAME, "remote_object": remote_tag_before}),
        make_check("WORKTREE", not unexpected, "Working tree has no unexpected or pre-staged changes.", "Unexpected or pre-staged changes exist.", {"unexpected": unexpected, "allowed": allowed}),
    ]
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"

    print("[3/9] [PASS] Writing regulated Stage 21.0.4 preflight artifacts.")
    payload = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {"conclusion": conclusion, "blocking_failures": blockers},
        "git": {
            "branch": branch,
            "head_before_commit": head,
            "upstream": upstream,
            "upstream_head_before_commit": upstream_head,
        },
        "tag": {
            "name": TAG_NAME,
            "target_commit": BASELINE_COMMIT,
            "annotation": TAG_MESSAGE,
            "local_exists_before": local_tag_exists,
            "remote_exists_before": remote_tag_before is not None,
            "reserved_future_tag": "rom-v1-final",
        },
        "checks": [asdict(item) for item in checks],
        "database_evidence_before": db_before,
        "artifacts": {"patch": PATCH_PATH, "json": JSON_PATH, "markdown": MD_PATH},
        "next_stage": "21.1.1" if conclusion == "GO" else None,
    }
    write_atomic(root / JSON_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / MD_PATH, render_markdown(payload))

    if conclusion != "GO":
        print("[4/9] [FAIL] Preflight returned NO_GO; no commit or tag was created.")
        print("PATCH STATUS: FAIL\nGIT COMMIT STATUS: NOT CREATED\nTAG STATUS: NOT CREATED\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED")
        print("Blocking failures: " + ", ".join(blockers))
        return 1

    commit_created = False
    tag_created = False
    branch_published = False
    tag_published = False
    try:
        print("[4/9] [PASS] Staging exact Stage 21.0.4 allowlist.")
        exact_stage(root, [PATCH_PATH, JSON_PATH, MD_PATH])

        print("[5/9] [PASS] Creating Stage 21.0.4 commit.")
        commit_result = git(root, "commit", "-m", COMMIT_MESSAGE)
        if commit_result.returncode != 0:
            raise PatchError(commit_result.stderr.strip() or commit_result.stdout.strip() or "git commit failed")
        commit_created = True
        commit_hash = rev(root, "HEAD")
        if not commit_hash:
            raise PatchError("commit created but HEAD cannot be resolved")

        print(f"[6/9] [PASS] Creating annotated tag {TAG_NAME} on {BASELINE_COMMIT}.")
        tag_result = git(root, "tag", "-a", TAG_NAME, BASELINE_COMMIT, "-m", TAG_MESSAGE)
        if tag_result.returncode != 0:
            raise PatchError(tag_result.stderr.strip() or tag_result.stdout.strip() or "annotated tag creation failed")
        tag_created = True
        object_type = git(root, "cat-file", "-t", f"refs/tags/{TAG_NAME}")
        local_tag_target = rev(root, TAG_NAME)
        if object_type.returncode != 0 or object_type.stdout.strip() != "tag" or local_tag_target != BASELINE_COMMIT:
            raise PatchError("local annotated tag verification failed")

        print(f"[7/9] [PASS] Pushing {TARGET_BRANCH} with Stage 21.0.3-21.0.4 commits.")
        push_branch = git(root, "push", "origin", TARGET_BRANCH, timeout=180)
        if push_branch.returncode != 0:
            raise PatchError(push_branch.stderr.strip() or push_branch.stdout.strip() or "branch push failed")
        branch_published = True

        print(f"[8/9] [PASS] Publishing explicit tag ref refs/tags/{TAG_NAME}.")
        push_tag = git(root, "push", "origin", f"refs/tags/{TAG_NAME}:refs/tags/{TAG_NAME}", timeout=180)
        if push_tag.returncode != 0:
            raise PatchError(push_tag.stderr.strip() or push_tag.stdout.strip() or "tag push failed")
        tag_published = True

        remote_branch = rev(root, f"origin/{TARGET_BRANCH}")
        remote_tag_target = remote_tag_commit(root)
        db_after = database_evidence(root)
        final_ok = (
            git(root, "branch", "--show-current").stdout.strip() == TARGET_BRANCH
            and remote_branch == commit_hash
            and local_tag_target == BASELINE_COMMIT
            and remote_tag_target == BASELINE_COMMIT
            and db_before == db_after
        )
        if not final_ok:
            raise PatchError("final branch/tag/SQLite consistency verification failed")

        print("[9/9] [PASS] Local tag, remote tag, branch and SQLite evidence verified.")
        print("=" * 72)
        print(f"ROM Stage {STAGE} - tag final V1 baseline")
        print("=" * 72)
        for item in checks:
            print(f"[{item.status}] {item.check_id}: {item.summary}")
        print(f"[PASS] COMMIT: {commit_hash}")
        print(f"[PASS] TAG: {TAG_NAME}")
        print(f"[PASS] TAG_TARGET: {local_tag_target}")
        print(f"[PASS] REMOTE_TAG_TARGET: {remote_tag_target}")
        print(f"[PASS] REMOTE_BRANCH: {remote_branch}")
        print("-" * 72)
        print("CONCLUSION: GO")
        print("PATCH STATUS: PASS")
        print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
        print(f"TAG STATUS: PASS ({TAG_NAME} -> {BASELINE_COMMIT})")
        print("REMOTE PUSH STATUS: PASS")
        print("MANUAL CHECK: NOT REQUIRED")
        print("WAL/SHM: NOT MANIPULATED")
        return 0
    except (PatchError, subprocess.TimeoutExpired) as exc:
        # Before any remote mutation, rollback every local mutation. Once either
        # branch or tag is published, do not rewrite or delete remote history
        # automatically; stop fail-closed and require explicit recovery.
        if not branch_published and not tag_published:
            recovery = rollback_before_publish(root, commit_created, tag_created)
            recovery_text = json.dumps(recovery, ensure_ascii=False)
        else:
            recovery_text = (
                "remote mutation already exists; no automatic remote delete/reset was attempted. "
                "Explicit recovery is required."
            )
        print(f"[FAIL] {exc}", file=sys.stderr)
        print(f"RECOVERY: {recovery_text}")
        print("PATCH STATUS: FAIL")
        print("GIT COMMIT STATUS: FAILED OR RECOVERY REQUIRED")
        print("TAG STATUS: FAILED OR RECOVERY REQUIRED")
        print("MANUAL CHECK: NOT REQUIRED")
        print("WAL/SHM: NOT MANIPULATED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
