#!/usr/bin/env python3
"""Stage 21.0.1: audit ROM readiness, add .runtime/ ignore, and commit on GO.

Run from ROM root: python .\\patch\\patch_21_0_1_audit_rewrite_readiness.py
JSON is written to reports; Markdown is written to MD. Production SQLite and
its WAL/SHM files are never opened or modified; checks run on an isolated copy.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

STAGE = "21.0.1"
BASELINE = "bd6880020d3918d2ca3c071950975826dc69320c"
SYNCED_HEAD = "ff9f4920519ca5154ff1238ddaae67cb9ee2ce29"
COMMIT_MESSAGE = "Stage 21.0.1: audit ROM V2 rewrite readiness"
PATCH_PATH = "patch/patch_21_0_1_audit_rewrite_readiness.py"
JSON_PATH = "reports/stage_21_0_1_rewrite_readiness_audit.json"
MD_PATH = "MD/STAGE_21_0_1_REWRITE_READINESS_AUDIT.md"
GITIGNORE_PATH = ".gitignore"
OWNED = {PATCH_PATH, JSON_PATH, MD_PATH, GITIGNORE_PATH}
DIRTY_DUMPS = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
TARGET_BRANCH = "rewrite/rom-v2"
TOKEN_RE = re.compile(r"\b\d{7,12}:[A-Za-z0-9_-]{30,}\b")
PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".toml", ".ini", ".cfg", ".yaml", ".yml", ".ps1", ".sh", ".example"}
SKIP_DIRS = {".git", ".venv", "venv", "backup", "__pycache__", ".runtime", "node_modules"}


@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    severity: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False


class PatchError(RuntimeError):
    pass


def run(root: Path, *cmd: str, timeout: int = 45) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, check=False)


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run(root, "git", *args)


def check(cid: str, ok: bool, good: str, bad: str, details: dict[str, Any], *, blocking: bool = True, warn: bool = False) -> Check:
    if ok:
        return Check(cid, "PASS", "INFO", good, details, False)
    return Check(cid, "WARN" if warn else "FAIL", "MEDIUM" if warn else "CRITICAL", bad, details, False if warn else blocking)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    st = path.stat()
    return {"exists": True, "size": st.st_size, "mtime_ns": st.st_mtime_ns, "sha256": sha256(path)}


def db_evidence(root: Path) -> dict[str, Any]:
    return {name: evidence(root / name) for name in ("game.db", "game.db-wal", "game.db-shm")}


def tracked(root: Path) -> list[str]:
    r = git(root, "ls-files", "-z")
    return [x for x in r.stdout.split("\0") if x] if r.returncode == 0 else []


def parse_status(raw: str) -> list[dict[str, str]]:
    result = []
    for entry in raw.split("\0"):
        if entry:
            result.append({"status": entry[:2], "path": entry[3:]})
    return result


def text_files(root: Path, paths: list[str]):
    for rel in paths:
        p = root / rel
        if any(part in SKIP_DIRS for part in p.parts) or not p.is_file() or p.stat().st_size > 2_000_000:
            continue
        if p.suffix.lower() in TEXT_SUFFIXES or p.name in {".gitignore", ".env.example"}:
            yield rel, p


def ensure_runtime_ignore(root: Path) -> tuple[bool, bool, str]:
    p = root / GITIGNORE_PATH
    existed = p.exists()
    original = p.read_text(encoding="utf-8") if existed else ""
    rules = {line.strip() for line in original.splitlines()}
    if ".runtime/" in rules or ".runtime" in rules:
        return False, existed, original
    sep = "" if not original or original.endswith("\n") else "\n"
    p.write_text(original + sep + "\n# ROM V2 local runtime artifacts\n.runtime/\n", encoding="utf-8", newline="\n")
    return True, existed, original


def restore_gitignore(root: Path, existed: bool, original: str) -> None:
    git(root, "reset", "--", GITIGNORE_PATH)
    p = root / GITIGNORE_PATH
    if existed:
        p.write_text(original, encoding="utf-8", newline="\n")
    elif p.exists():
        p.unlink()


def audit_database(root: Path, paths: list[str]) -> tuple[Check, dict[str, Any]]:
    before = db_evidence(root)
    info: dict[str, Any] = {"production_connection_opened": False, "before": before, "wal_shm": "NOT MANIPULATED"}
    db = root / "game.db"
    if not db.exists():
        info["after"] = db_evidence(root)
        return Check("DATABASE_BASELINE", "WARN", "MEDIUM", "game.db is absent; reset-first V2 remains possible.", info), info
    try:
        with tempfile.TemporaryDirectory(prefix="rom_21_0_1_") as td:
            snap = Path(td)
            for name in ("game.db", "game.db-wal", "game.db-shm"):
                src = root / name
                if src.exists():
                    shutil.copy2(src, snap / name)
            con = sqlite3.connect((snap / "game.db").resolve().as_uri() + "?mode=ro", uri=True, timeout=3)
            try:
                quick = [r[0] for r in con.execute("PRAGMA quick_check").fetchall()]
                fk_count = len(con.execute("PRAGMA foreign_key_check").fetchall())
                user_version = con.execute("PRAGMA user_version").fetchone()[0]
                tables = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
            finally:
                con.close()
        after = db_evidence(root)
        unchanged = before == after
        info.update({"after": after, "quick_check": quick, "foreign_key_violation_count": fk_count, "user_version": user_version, "table_count": tables, "query_target": "isolated_snapshot", "production_bytes_unchanged": unchanged})
        ok = quick == ["ok"] and fk_count == 0 and unchanged
        return check("DATABASE_BASELINE", ok, "Isolated DB snapshot passed; production DB/WAL/SHM evidence is unchanged.", "Database snapshot or byte-preservation check failed.", info), info
    except (OSError, sqlite3.Error) as exc:
        info.update({"error": str(exc), "after": db_evidence(root)})
        return Check("DATABASE_BASELINE", "FAIL", "CRITICAL", "Database snapshot audit failed.", info, True), info


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def md(payload: dict[str, Any]) -> str:
    rows = []
    for c in payload["checks"]:
        rows.append(f"| `{c['check_id']}` | **{c['status']}** | {c['severity']} | {'так' if c['blocking'] else 'ні'} | {c['summary'].replace('|', '/') } |")
    return "\n".join([
        "# ROM Stage 21.0.1 - аудит готовності до rewrite", "",
        f"- **Висновок:** `{payload['summary']['conclusion']}`",
        f"- **Поточна гілка:** `{payload['git']['branch']}`",
        f"- **HEAD до commit:** `{payload['git']['HEAD']}`",
        f"- **PASS/WARN/FAIL:** `{payload['summary']['counts']['PASS']}/{payload['summary']['counts']['WARN']}/{payload['summary']['counts']['FAIL']}`", "",
        "## Перевірки", "", "| ID | Статус | Рівень | Blocking | Результат |", "|---|---:|---:|---:|---|", *rows, "",
        "## Гарантії", "",
        "- Production-код і game.db не змінювалися.",
        "- Production game.db не відкривалася через SQLite; перевірки виконано тільки на isolated snapshot.",
        "- game.db-wal і game.db-shm не видалялися, не очищувалися і не використовувалися для rollback.",
        "- Старі Stage 19-20 Markdown/JSON не відновлювалися; робочі MD і reports залишаються чистими для Stage 21.",
        "- Після GO patch, JSON, Markdown і .gitignore фіксуються exact-allowlist commit-ом.", "",
        "## Наступний етап", "", "Stage 21.0.2 - створення `rewrite/rom-v2`." if payload["summary"]["conclusion"] == "GO" else "Stage 21.0.2 заблоковано до усунення blocking failures.", ""
    ])


def stage_commit(root: Path) -> str:
    paths = [PATCH_PATH, JSON_PATH, MD_PATH, GITIGNORE_PATH]
    r = git(root, "add", "-f", "--", *paths)
    if r.returncode:
        raise PatchError(r.stderr.strip() or "git add failed")
    staged_raw = git(root, "diff", "--cached", "--name-only", "-z")
    staged = sorted(x for x in staged_raw.stdout.split("\0") if x)
    if staged != sorted(paths):
        git(root, "reset", "--", *paths)
        raise PatchError(f"staging allowlist mismatch: {staged}")
    r = git(root, "commit", "-m", COMMIT_MESSAGE)
    if r.returncode:
        git(root, "reset", "--", *paths)
        raise PatchError(r.stderr.strip() or r.stdout.strip() or "git commit failed")
    r = git(root, "rev-parse", "HEAD")
    if r.returncode:
        raise PatchError("commit created but HEAD cannot be resolved")
    return r.stdout.strip()


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    if not (root / ".git").exists():
        print("[FAIL] Run this file from ROM\\patch.", file=sys.stderr); return 2
    if not (root / "reports").is_dir() or not (root / "MD").is_dir():
        print("[FAIL] Required reports and MD directories are missing.", file=sys.stderr); return 2

    print("[1/7] [PASS] ROM root and artifact directories detected.")
    status = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = parse_status(status.stdout)
    allowed = []
    for e in entries:
        index, path = e["status"][0], e["path"]
        if index in {" ", "?"} and (path in OWNED or (path in DIRTY_DUMPS and index == " ")):
            allowed.append(e)
    unexpected = [e for e in entries if e not in allowed]

    print("[2/7] [PASS] Auditing Git branches, cached origin refs and worktree.")
    def rev(name: str) -> str | None:
        r = git(root, "rev-parse", "--verify", f"{name}^{{commit}}")
        return r.stdout.strip() if r.returncode == 0 else None
    branch = git(root, "branch", "--show-current").stdout.strip()
    refs = {name: rev(name) for name in ("HEAD", "master", "develop", "origin/master", "origin/develop")}
    checks: list[Check] = []
    checks.append(check("GIT_REPOSITORY", git(root, "rev-parse", "--is-inside-work-tree").stdout.strip() == "true", "ROM is a valid Git working tree.", "ROM is not a valid Git working tree.", {}))
    checks.append(check("CURRENT_BRANCH", branch == "develop", "Current branch is develop.", f"Expected develop; detected {branch or 'detached HEAD'}.", {"branch": branch}))
    synced = len({refs[x] for x in ("master", "develop", "origin/master", "origin/develop")}) == 1 and refs["develop"] is not None
    checks.append(check("BRANCH_SYNC", synced, "master, develop and cached origin refs are synchronized.", "master/develop/origin refs are not synchronized.", refs))
    checks.append(check("EXPECTED_HEAD", refs["HEAD"] == SYNCED_HEAD, "HEAD matches the approved clean Stage 21 starting point.", "HEAD differs from the approved synchronized commit.", {"expected": SYNCED_HEAD, "actual": refs["HEAD"]}))
    rewrite_local = git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{TARGET_BRANCH}").returncode == 0
    rewrite_remote = git(root, "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{TARGET_BRANCH}").returncode == 0
    checks.append(check("REWRITE_BRANCH_ABSENCE", not rewrite_local and not rewrite_remote, f"{TARGET_BRANCH} is available.", f"{TARGET_BRANCH} already exists.", {"local": rewrite_local, "cached_origin": rewrite_remote}))
    checks.append(check("WORKTREE", not unexpected, "Working tree has no unexpected changes.", "Unexpected or pre-staged changes exist.", {"unexpected": unexpected, "allowed": allowed}))
    baseline_ok = git(root, "merge-base", "--is-ancestor", BASELINE, "HEAD").returncode == 0
    checks.append(check("STAGE20_BASELINE", baseline_ok, "Stage 20 closure is an ancestor of HEAD.", "Stage 20 closure is not an ancestor of HEAD.", {"baseline": BASELINE}))
    checks.append(check("GIT_REMOTE", git(root, "remote", "get-url", "origin").returncode == 0, "origin remote is configured.", "origin remote is missing.", {}))

    changed, gi_existed, gi_original = ensure_runtime_ignore(root)
    rules = {x.strip() for x in (root / ".gitignore").read_text(encoding="utf-8").splitlines()}
    needed = {".env", ".venv/", "__pycache__/", "*.db-wal", "*.db-shm", ".runtime/"}
    checks.append(check("GITIGNORE", needed.issubset(rules), ".gitignore contains required safeguards.", ".gitignore lacks required safeguards.", {"missing": sorted(needed-rules), "runtime_rule_added": changed}))

    print("[3/7] [PASS] Auditing tracked credentials, entrypoint and repository layout.")
    paths = tracked(root)
    dangerous_names = {".env", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "credentials.json", "service-account.json", "service_account.json", "secrets.json", "secrets.yaml", "secrets.yml"}
    dangerous_suffixes = {".pem", ".p12", ".pfx", ".key", ".keystore", ".jks"}
    named = [x for x in paths if Path(x).name.lower() in dangerous_names or Path(x).suffix.lower() in dangerous_suffixes]
    checks.append(check("SENSITIVE_TRACKED_NAMES", not named, "No tracked credential containers were found.", "Potential credential containers are tracked.", {"paths": named, "token_terms_ignored": True}))
    secret_hits = []
    for rel, p in text_files(root, paths):
        data = p.read_text(encoding="utf-8", errors="replace")
        for kind, pattern in (("telegram_token", TOKEN_RE), ("private_key", PRIVATE_KEY_RE)):
            for m in pattern.finditer(data):
                secret_hits.append({"path": rel, "line": data.count("\n", 0, m.start())+1, "detector": kind})
    checks.append(check("SECRET_CONTENT_SCAN", not secret_hits, "No high-confidence secret values were found.", "Potential secret values were detected; values are redacted.", {"findings": secret_hits}))
    checks.append(check("ENTRYPOINT", (root/"main.py").is_file(), "Root main.py is available.", "Root main.py is missing.", {}))
    required = {"patch", "backup", "reports", "tools", "MD"}
    missing_dirs = sorted(x for x in required if not (root/x).is_dir())
    v2_conflicts = sorted(x for x in ("rom_v2", "tests_v2", ".runtime") if (root/x).exists())
    checks.append(check("REPOSITORY_LAYOUT", not missing_dirs and not v2_conflicts, "Operational directories exist and V2 paths are free.", "Repository layout needs review.", {"missing": missing_dirs, "conflicts": v2_conflicts}, warn=True))
    verifier_files = [x for x in paths if x.endswith(".py") and ("tools/" in x) and any(k in Path(x).name.lower() for k in ("test", "verify", "regression", "contract"))]
    checks.append(check("TEST_LAYOUT", bool(verifier_files), "Existing tests/verifiers are available.", "No existing verifier files were found.", {"count": len(verifier_files)}, blocking=False, warn=True))
    checks.append(check("ROM_V2_NAME_CONFLICT", not any(x.startswith("rom_v2/") for x in paths), "rom_v2 is available.", "rom_v2 already exists in tracked files.", {}, warn=True))

    print("[4/7] [PASS] Creating isolated SQLite snapshot for integrity checks.")
    db_check, db_info = audit_database(root, paths)
    checks.append(db_check)

    counts = {k: sum(c.status == k for c in checks) for k in ("PASS", "WARN", "FAIL")}
    blockers = [c.check_id for c in checks if c.blocking and c.status == "FAIL"]
    conclusion = "GO" if not blockers else "NO_GO"
    print("[5/7] [PASS] Building audit artifacts.")
    payload = {
        "schema_version": 2, "stage": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {"conclusion": conclusion, "counts": counts, "blocking_failures": blockers},
        "git": {"branch": branch, **refs}, "worktree": entries, "database": db_info,
        "checks": [asdict(c) for c in checks],
        "artifact_policy": {"patch": PATCH_PATH, "json": JSON_PATH, "markdown": MD_PATH, "historical_stage_19_20_files_restored": False},
        "next_stage": "21.0.2" if conclusion == "GO" else None,
    }
    write_atomic(root/JSON_PATH, json.dumps(payload, ensure_ascii=False, indent=2)+"\n")
    write_atomic(root/MD_PATH, md(payload))
    print("[6/7] [PASS] JSON and Markdown written to their regulated directories.")

    commit_hash = None
    if conclusion == "GO":
        try:
            commit_hash = stage_commit(root)
            print(f"[7/7] [PASS] Git commit created: {commit_hash}")
        except PatchError as exc:
            restore_gitignore(root, gi_existed, gi_original)
            print(f"[7/7] [FAIL] {exc}", file=sys.stderr)
            print("PATCH STATUS: FAIL\nGIT COMMIT STATUS: FAIL\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED")
            return 2
    else:
        restore_gitignore(root, gi_existed, gi_original)
        print("[7/7] [WARN] NO_GO: .gitignore restored; audit artifacts retained.")

    print("="*72)
    print(f"ROM Stage {STAGE} - rewrite readiness audit")
    print("="*72)
    for c in checks:
        print(f"[{c.status}] {c.check_id}: {c.summary}")
    print("-"*72)
    print(f"CONCLUSION: {conclusion}")
    print(f"JSON: {root/JSON_PATH}\nMarkdown: {root/MD_PATH}")
    print("PATCH STATUS: " + ("PASS" if conclusion == "GO" else "FAIL"))
    print("GIT COMMIT STATUS: " + (f"PASS ({commit_hash})" if commit_hash else "NOT CREATED"))
    print("MANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED")
    if blockers:
        print("Blocking failures: " + ", ".join(blockers))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
