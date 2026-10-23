#!/usr/bin/env python3
"""ROM Stage 21.10.2d: correct Crystal Wallet/Ledger metadata labels.

This metadata-only patch renames the incorrectly numbered Markdown artifact and
corrects the targeted-smoke label in the Stage 21.10.2c machine report; the previously dirty Stage 21.9.6c document and dump are already committed separately. It does
not modify production code, tests, databases, runtime wiring, or persistence.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STAGE = "21.10.2d"
BRANCH = "rewrite/rom-v2"
PARENT = "ca8ddf269c58e61a8edc5d9eef78a5659b816852"
REPORT = Path("reports/stage_21_10_2c_crystal_wallet_ledger_implementation.json")
OLD_DOC = Path("MD/STAGE_21_10_1C_CRYSTAL_WALLET_LEDGER_IMPLEMENTATION.md")
NEW_DOC = Path("MD/STAGE_21_10_2C_CRYSTAL_WALLET_LEDGER_IMPLEMENTATION.md")
FAILURE = Path("reports/stage_21_10_2d_failure_rollback.json")
SELF = Path("patch/patch_21_10_2d_fix_crystal_wallet_ledger_metadata.py")
MUTATION_TARGETS = (REPORT, OLD_DOC, NEW_DOC, SELF)
# Git reports this same-content move as the new path only in --name-only output.
EXPECTED_COMMIT_PATHS = {REPORT.as_posix(), NEW_DOC.as_posix(), SELF.as_posix()}
OLD_SMOKE = "STAGE_21_10_1C_CRYSTAL_WALLET_LEDGER_SMOKE: PASS"
NEW_SMOKE = "STAGE_21_10_2C_CRYSTAL_WALLET_LEDGER_SMOKE: PASS"
ALLOWED_DIRTY = {
    "reports/stage_21_10_1_failure_rollback.json",
    "reports/stage_21_10_1a_failure_rollback.json",
    "reports/stage_21_10_1c_failure_rollback.json",
    "reports/stage_21_10_2_failure_rollback.json",
    FAILURE.as_posix(),
    "reports/v2_ci_failure.json",
    "reports/v2_ci_result.json",
}
PROTECTED = (
    "game.db", "game.db-wal", "game.db-shm", ".env", "rom_v2/.env",
    ".runtime/v2/db/rom_v2.db",
)


class PatchError(RuntimeError):
    """Raised when a mandatory metadata correction or safety gate fails."""


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


def protected_snapshot(root):
    snapshot = {name: sha(root / name) for name in PROTECTED}
    for base_name in ("rom_v2", "tests_v2", "tools"):
        base = root / base_name
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            snapshot[path.relative_to(root).as_posix()] = sha(path)
    return snapshot


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
    if git(root, "diff", "--cached", "--name-only").stdout.strip():
        raise PatchError("index_not_clean")
    dirty = status_paths(root)
    if not dirty.issubset(ALLOWED_DIRTY):
        raise PatchError(f"unexpected_dirty:{sorted(dirty - ALLOWED_DIRTY)}")
    if not (root / REPORT).is_file():
        raise PatchError("missing_stage_21_10_2c_report")
    if not (root / OLD_DOC).is_file():
        raise PatchError("missing_incorrectly_named_stage_21_10_1c_doc")
    if (root / NEW_DOC).exists():
        raise PatchError("correctly_named_doc_already_exists")
    payload = json.loads((root / REPORT).read_text(encoding="utf-8"))
    if (payload.get("stage"), payload.get("status"), payload.get("conclusion")) != (
        "21.10.2c", "PASS", "API_READY"
    ):
        raise PatchError("invalid_stage_21_10_2c_report")
    smoke = payload.get("verification", {}).get("targeted_smoke")
    if smoke != OLD_SMOKE:
        raise PatchError(f"unexpected_targeted_smoke:{smoke}")
    document = (root / OLD_DOC).read_text(encoding="utf-8")
    if "# Stage 21.10.2c" not in document:
        raise PatchError("unexpected_markdown_stage_content")
    return payload


def backup(root):
    folder = root / "backup" / f"stage_21_10_2d_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    folder.mkdir(parents=True, exist_ok=False)
    state = {}
    for relative in MUTATION_TARGETS:
        source = root / relative
        state[relative.as_posix()] = source.exists()
        if source.exists():
            destination = folder / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    return folder, state


def restore(root, folder, state):
    git(root, "reset", "--mixed", check=False)
    restored = []
    if folder is None:
        return restored
    for relative in MUTATION_TARGETS:
        destination = root / relative
        saved = folder / relative
        existed = state.get(relative.as_posix(), False)
        if existed and saved.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(saved, destination)
            restored.append(relative.as_posix())
        elif not existed and destination.exists():
            destination.unlink()
            restored.append(relative.as_posix())
    return restored


def clean_bytecode(root):
    """Remove generated bytecode before content validation without touching production source."""
    removed = []
    for base_name in ("rom_v2", "tests_v2", "tools"):
        base = root / base_name
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.pyc")):
            path.unlink(missing_ok=True)
            removed.append(path.relative_to(root).as_posix())
        for directory in sorted(
            base.rglob("__pycache__"), key=lambda item: len(item.parts), reverse=True
        ):
            try:
                directory.rmdir()
            except OSError:
                pass
    return removed


def run_ci(root, environment):
    temporary = root / "reports/.stage_21_10_2d_ci.tmp.json"
    temporary.unlink(missing_ok=True)
    process = run([
        sys.executable, "-B", "tools/run_v2_ci.py", "--project-root", str(root),
        "--json-out", str(temporary),
    ], root, False, environment)
    if not temporary.is_file():
        raise PatchError(f"ci_report_missing:{process.stderr[-1200:]}")
    result = json.loads(temporary.read_text(encoding="utf-8"))
    temporary.unlink(missing_ok=True)
    if process.returncode or result.get("status") != "PASS":
        raise PatchError(f"canonical_ci_failed:{json.dumps(result, ensure_ascii=False)}")
    return result


def main():
    root = Path(__file__).resolve().parents[1]
    folder = None
    state = {}
    try:
        payload = preflight(root)
        print("[1/10] [PASS] Stage 21.10.2c API-ready report and metadata defect verified.")
        print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
        before = protected_snapshot(root)
        folder, state = backup(root)
        print("[3/10] [PASS] Report, old/new documentation paths and patch backed up before mutation.")

        payload["verification"]["targeted_smoke"] = NEW_SMOKE
        (root / REPORT).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (root / NEW_DOC).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(root / OLD_DOC, root / NEW_DOC)
        print("[4/10] [PASS] Targeted-smoke stage label corrected to 21.10.2c.")
        print("[5/10] [PASS] Markdown artifact renamed from 21.10.1c to 21.10.2c.")

        corrected = json.loads((root / REPORT).read_text(encoding="utf-8"))
        if corrected.get("verification", {}).get("targeted_smoke") != NEW_SMOKE:
            raise PatchError("targeted_smoke_correction_not_persisted")
        if (root / OLD_DOC).exists() or not (root / NEW_DOC).is_file():
            raise PatchError("markdown_rename_not_persisted")
        if "# Stage 21.10.2c" not in (root / NEW_DOC).read_text(encoding="utf-8"):
            raise PatchError("renamed_markdown_content_changed")
        print("[6/10] [PASS] Corrected JSON and Markdown metadata contract verified.")

        removed_bytecode = clean_bytecode(root)
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONHASHSEED"] = "0"
        ci = run_ci(root, environment)
        print(
            f"[7/10] [PASS] Canonical six-gate V2 CI passed after removing "
            f"{len(removed_bytecode)} generated bytecode artifacts."
        )
        after = protected_snapshot(root)
        if before != after:
            changed = sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))
            raise PatchError(f"protected_runtime_changed:{changed}")
        print("[8/10] [PASS] Production/test/tool sources, DB sidecars and protected configuration remained byte-identical.")

        if corrected.get("stage") != "21.10.2c" or corrected.get("conclusion") != "API_READY":
            raise PatchError("corrected_report_semantics_changed")
        if ci.get("status") != "PASS":
            raise PatchError("canonical_ci_not_pass")
        print("[9/10] [PASS] Stage 21.10.2c API-ready semantics remained unchanged.")

        git(
            root, "add", "-f", "-A", "--",
            REPORT.as_posix(), OLD_DOC.as_posix(), NEW_DOC.as_posix(),
            SELF.as_posix(),
        )
        staged = {
            line.strip().replace("\\", "/")
            for line in git(root, "diff", "--cached", "--name-only").stdout.splitlines()
            if line.strip()
        }
        if staged != EXPECTED_COMMIT_PATHS:
            raise PatchError(f"staging_mismatch:{sorted(staged)}")
        commit_result = git(
            root, "commit", "-m", "Stage 21.10.2d: fix Crystal Wallet/Ledger metadata",
            check=False,
        )
        if commit_result.returncode:
            raise PatchError(f"commit_failed:{commit_result.stdout}:{commit_result.stderr}")
        commit = git(root, "rev-parse", "HEAD").stdout.strip()
        changed = {
            line.strip().replace("\\", "/")
            for line in git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout.splitlines()
            if line.strip()
        }
        if changed != EXPECTED_COMMIT_PATHS:
            raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
        (root / FAILURE).unlink(missing_ok=True)
        print(f"[10/10] [PASS] Crystal Wallet/Ledger metadata correction committed: {commit}")
        print("CONCLUSION: METADATA_CORRECTED")
        print("PATCH STATUS: PASS")
        print(f"GIT COMMIT STATUS: PASS ({commit})")
        print("STAGE 21.10.2c STATUS: API_READY_UNCHANGED")
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
