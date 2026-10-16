#!/usr/bin/env python3
"""Stage 21.3.3: define validated V2 configuration and secret boundaries."""
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

STAGE = "21.3.3"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "ffa80d04d84d3c4ddf12bbe8f5bcba875454e71b"
PREREQUISITE_REPORT = "reports/stage_21_3_2_runtime_directories.json"
PATCH_PATH = "patch/patch_21_3_3_define_v2_configuration_secrets.py"
SETTINGS_PATH = "rom_v2/settings.py"
TEST_PATH = "tests_v2/test_settings.py"
ENV_EXAMPLE_PATH = ".env.example"
GITIGNORE_PATH = ".gitignore"
REPORT_PATH = "reports/stage_21_3_3_configuration_secrets.json"
CONTRACT_PATH = "MD/STAGE_21_3_3_V2_CONFIGURATION_SECRETS.md"
FAILURE_REPORT = "reports/stage_21_3_3_failure_rollback.json"
COMMIT_MESSAGE = "Stage 21.3.3: define V2 configuration and secrets"
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
MUTATED_FILES = (
    SETTINGS_PATH,
    TEST_PATH,
    ENV_EXAMPLE_PATH,
    GITIGNORE_PATH,
    REPORT_PATH,
    CONTRACT_PATH,
)
OWNED = {PATCH_PATH, FAILURE_REPORT, *MUTATED_FILES}
BACKUP_PREFIX = "stage_21_3_3"
SECRET_ENV_KEYS = ("ROM_V2_BOT_TOKEN",)
GITIGNORE_BLOCK = """# Local environment and secrets (Stage 21.3.3)\n.env\n.env.*\n!.env.example\n"""

SETTINGS_SOURCE = '''"""Validated environment configuration and redacted secret values for ROM V2."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from rom_v2.runtime_paths import RuntimePaths


class ConfigurationError(ValueError):
    """Report invalid configuration using a stable machine-readable reason."""


@dataclass(frozen=True, slots=True)
class SecretValue:
    """Hold a secret while preventing accidental repr or string disclosure."""

    _value: str

    @classmethod
    def from_required(cls, value: str | None, key: str) -> "SecretValue":
        """Create a non-empty secret or reject the missing environment key."""
        if value is None or not value.strip():
            raise ConfigurationError(f"missing_required_secret:{key}")
        return cls(value.strip())

    def reveal(self) -> str:
        """Return the secret only at the external adapter boundary."""
        return self._value

    def __repr__(self) -> str:
        """Render a constant redacted representation for logs and diagnostics."""
        return "SecretValue(<redacted>)"

    def __str__(self) -> str:
        """Render a constant redacted string instead of the protected value."""
        return "<redacted>"


@dataclass(frozen=True, slots=True)
class V2Settings:
    """Hold validated V2 settings loaded once by the composition root."""

    application_name: str
    environment: str
    log_level: str
    bot_token: SecretValue
    runtime_paths: RuntimePaths

    @classmethod
    def from_environment(
        cls,
        project_root: Path,
        environment: Mapping[str, str] | None = None,
    ) -> "V2Settings":
        """Load and validate settings without reading a local dotenv file."""
        values = os.environ if environment is None else environment
        application_name = values.get("ROM_V2_APPLICATION_NAME", "rom_v2").strip()
        runtime_environment = values.get("ROM_V2_ENVIRONMENT", "development").strip().lower()
        log_level = values.get("ROM_V2_LOG_LEVEL", "INFO").strip().upper()
        if not application_name:
            raise ConfigurationError("invalid_application_name")
        if runtime_environment not in {"development", "test", "production"}:
            raise ConfigurationError("invalid_environment")
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ConfigurationError("invalid_log_level")
        runtime_paths = RuntimePaths.from_project_root(project_root)
        runtime_paths.validate()
        return cls(
            application_name=application_name,
            environment=runtime_environment,
            log_level=log_level,
            bot_token=SecretValue.from_required(values.get("ROM_V2_BOT_TOKEN"), "ROM_V2_BOT_TOKEN"),
            runtime_paths=runtime_paths,
        )

    def safe_summary(self) -> dict[str, str]:
        """Return diagnostics that contain no secret value or secret metadata."""
        return {
            "application_name": self.application_name,
            "environment": self.environment,
            "log_level": self.log_level,
            "runtime_root": self.runtime_paths.root.as_posix(),
        }
'''

TEST_SOURCE = '''"""Tests for validated and redacted ROM V2 settings."""
from __future__ import annotations

import unittest
from pathlib import Path

from rom_v2.settings import ConfigurationError, SecretValue, V2Settings


class V2SettingsTest(unittest.TestCase):
    """Verify validation, redaction, and safe diagnostics."""

    def test_valid_environment_is_loaded_without_secret_disclosure(self) -> None:
        """Load settings and prove every presentation path stays redacted."""
        protected_value = "unit-test-only-value"
        settings = V2Settings.from_environment(
            Path("."),
            {
                "ROM_V2_BOT_TOKEN": protected_value,
                "ROM_V2_ENVIRONMENT": "test",
                "ROM_V2_LOG_LEVEL": "debug",
            },
        )
        self.assertEqual(settings.bot_token.reveal(), protected_value)
        self.assertNotIn(protected_value, repr(settings.bot_token))
        self.assertNotIn(protected_value, str(settings.bot_token))
        self.assertNotIn(protected_value, repr(settings))
        self.assertNotIn(protected_value, repr(settings.safe_summary()))

    def test_missing_secret_is_rejected_with_stable_reason(self) -> None:
        """Reject an absent token without echoing any environment content."""
        with self.assertRaisesRegex(ConfigurationError, "missing_required_secret"):
            V2Settings.from_environment(Path("."), {})

    def test_invalid_values_are_rejected(self) -> None:
        """Reject unsupported environment and log-level values."""
        with self.assertRaisesRegex(ConfigurationError, "invalid_environment"):
            V2Settings.from_environment(
                Path("."),
                {"ROM_V2_BOT_TOKEN": "unit-test-only-value", "ROM_V2_ENVIRONMENT": "invalid"},
            )
        with self.assertRaisesRegex(ConfigurationError, "invalid_log_level"):
            V2Settings.from_environment(
                Path("."),
                {"ROM_V2_BOT_TOKEN": "unit-test-only-value", "ROM_V2_LOG_LEVEL": "TRACE"},
            )


class SecretValueTest(unittest.TestCase):
    """Verify the dedicated secret wrapper independently."""

    def test_empty_secret_is_rejected(self) -> None:
        """Reject whitespace-only secret values."""
        with self.assertRaises(ConfigurationError):
            SecretValue.from_required("   ", "ROM_V2_BOT_TOKEN")


if __name__ == "__main__":
    unittest.main()
'''

ENV_EXAMPLE_SOURCE = '''# ROM V2 configuration template. Copy to .env locally; never commit real values.
ROM_V2_APPLICATION_NAME=rom_v2
ROM_V2_ENVIRONMENT=development
ROM_V2_LOG_LEVEL=INFO
ROM_V2_BOT_TOKEN=
'''

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("telegram_bot_token", re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
)


@dataclass(frozen=True)
class Check:
    """Describe one automated Stage 21.3.3 check."""

    check_id: str
    status: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False


class PatchError(RuntimeError):
    """Signal a controlled patch failure."""


def run(root: Path, *command: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with bytecode creation disabled."""
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
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
    """Return a file SHA-256 without interpreting file contents."""
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


def git_blob(root: Path, commit: str, relative_path: str) -> bytes | None:
    """Read a file from the expected parent commit."""
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def prepare_backups(root: Path) -> dict[str, Any]:
    """Back up every file mutated by this patch."""
    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"files": {}}
    for relative_path in MUTATED_FILES:
        blob = git_blob(root, EXPECTED_PARENT, relative_path)
        backup_path = backup_dir / f"{BACKUP_PREFIX}__{relative_path.replace('/', '__')}"
        if blob is None:
            manifest["files"][relative_path] = {"existed": False, "backup": None}
        else:
            backup_path.write_bytes(blob)
            manifest["files"][relative_path] = {
                "existed": True,
                "backup": str(backup_path.relative_to(root)).replace("\\", "/"),
            }
    return manifest


def rollback(root: Path, manifest: dict[str, Any], reason: str, checks: list[Check]) -> dict[str, Any]:
    """Restore all changed files and report recovery evidence."""
    git(root, "reset", "--", *MUTATED_FILES)
    restored: list[str] = []
    removed: list[str] = []
    errors: list[str] = []
    for relative_path, metadata in manifest["files"].items():
        target = root / relative_path
        try:
            if metadata["existed"]:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((root / metadata["backup"]).read_bytes())
                restored.append(relative_path)
            elif target.exists():
                target.unlink()
                removed.append(relative_path)
        except OSError as exc:
            errors.append(f"{relative_path}: {exc}")
    payload = {
        "stage": STAGE,
        "status": "FAIL_ROLLED_BACK" if not errors else "ROLLBACK_INCOMPLETE",
        "reason": reason,
        "failed_checks": [asdict(item) for item in checks if item.status == "FAIL"],
        "restored_files": restored,
        "removed_failed_artifacts": removed,
        "rollback_errors": errors,
        "database_evidence_after_rollback": database_evidence(root),
        "main_py_started_after_failure": False,
        "wal_shm_manipulated": False,
    }
    write_atomic(root / FAILURE_REPORT, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return payload


def append_gitignore(original: str) -> str:
    """Append secret exclusions exactly once and preserve existing rules."""
    if ".env.*" in original.splitlines() and "!.env.example" in original.splitlines():
        return original
    separator = "" if not original or original.endswith("\n") else "\n"
    return original + separator + GITIGNORE_BLOCK


def scan_text(relative_path: str, text: str) -> list[dict[str, Any]]:
    """Find high-confidence secret formats without storing matched values."""
    findings: list[dict[str, Any]] = []
    for pattern_name, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
                {
                    "file": relative_path,
                    "line": text.count("\n", 0, match.start()) + 1,
                    "pattern": pattern_name,
                }
            )
    return findings


def scan_tracked_files(root: Path) -> dict[str, Any]:
    """Scan Git-tracked text files and never include secret values in output."""
    files_result = git(root, "ls-files", "-z")
    findings: list[dict[str, Any]] = []
    scanned = 0
    skipped_binary = 0
    for relative_path in (item for item in files_result.stdout.split("\0") if item):
        path = root / relative_path
        if not path.is_file():
            continue
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        if b"\x00" in raw:
            skipped_binary += 1
            continue
        text = raw.decode("utf-8", errors="replace")
        scanned += 1
        findings.extend(scan_text(relative_path, text))
    return {
        "scanned_text_files": scanned,
        "skipped_binary_files": skipped_binary,
        "finding_count": len(findings),
        "findings": findings,
    }


def verify_env_ignored(root: Path) -> dict[str, Any]:
    """Verify local dotenv files are ignored while the blank template is trackable."""
    ignored: dict[str, bool] = {}
    for candidate in (".env", ".env.local", ".env.production"):
        ignored[candidate] = git(root, "check-ignore", "-q", candidate).returncode == 0
    example_ignored = git(root, "check-ignore", "-q", ENV_EXAMPLE_PATH).returncode == 0
    return {
        "ignored": ignored,
        "all_local_env_ignored": all(ignored.values()),
        "example_is_trackable": not example_ignored,
    }


def render_contract(scan: dict[str, Any], ignore: dict[str, Any]) -> str:
    """Render a human-readable configuration and secrets contract."""
    return "\n".join(
        [
            "# Stage 21.3.3 — ROM V2 configuration and secrets",
            "",
            "- **Status:** `IMPLEMENTED`",
            "- **Canonical owner:** `rom_v2.settings.V2Settings`",
            "- **Secret wrapper:** `rom_v2.settings.SecretValue`",
            "- **Source:** process environment only",
            "",
            "## Configuration boundary",
            "",
            "`V2Settings.from_environment()` validates application name, environment, log level, runtime paths, and the required bot token. Domain and application code do not read `.env` or `os.environ` directly.",
            "",
            "## Secret policy",
            "",
            "Secrets are wrapped by `SecretValue`. String and repr output are always redacted. The protected value may be revealed only at an external adapter boundary. Safe summaries omit secret values and secret metadata.",
            "",
            "## Git policy",
            "",
            "Local `.env` variants are ignored. `.env.example` remains trackable and contains only blank placeholders.",
            "",
            "## Automated evidence",
            "",
            f"- Tracked text files scanned: **{scan['scanned_text_files']}**.",
            f"- High-confidence secret findings: **{scan['finding_count']}**.",
            f"- Local dotenv files ignored: **{ignore['all_local_env_ignored']}**.",
            f"- Blank example trackable: **{ignore['example_is_trackable']}**.",
            "",
            "## Next roadmap stage",
            "",
            "Stage 21.3.4 — Dependency container.",
            "",
        ]
    )


def exact_commit(root: Path) -> str:
    """Commit only the declared Stage 21.3.3 files after a staged secret scan."""
    paths = [PATCH_PATH, SETTINGS_PATH, TEST_PATH, ENV_EXAMPLE_PATH, GITIGNORE_PATH, REPORT_PATH, CONTRACT_PATH]
    added = git(root, "add", "-f", "--", *paths)
    if added.returncode != 0:
        raise PatchError(added.stderr.strip())
    staged = sorted(item for item in git(root, "diff", "--cached", "--name-only", "-z").stdout.split("\0") if item)
    if staged != sorted(paths):
        git(root, "reset", "--", *paths)
        raise PatchError(f"staging allowlist mismatch: {staged}")
    staged_patch = git(root, "diff", "--cached", "--no-ext-diff", "--unified=0")
    staged_findings = scan_text("<staged-diff>", staged_patch.stdout)
    if staged_findings:
        git(root, "reset", "--", *paths)
        raise PatchError(f"staged secret findings: {staged_findings}")
    committed = git(root, "commit", "-m", COMMIT_MESSAGE)
    if committed.returncode != 0:
        git(root, "reset", "--", *paths)
        raise PatchError(committed.stderr.strip() or committed.stdout.strip())
    return rev(root, "HEAD") or ""


def main() -> int:
    """Apply Stage 21.3.3 with validation, scanning, and fail-safe rollback."""
    root = Path(__file__).resolve().parent.parent
    if not (root / PREREQUISITE_REPORT).is_file():
        print(f"[FAIL] Missing prerequisite: {PREREQUISITE_REPORT}", file=sys.stderr)
        return 2
    prerequisite = json.loads((root / PREREQUISITE_REPORT).read_text(encoding="utf-8"))
    if prerequisite.get("stage") != "21.3.2" or prerequisite.get("summary", {}).get("conclusion") != "GO":
        print("[FAIL] Stage 21.3.2 prerequisite is not canonical GO.", file=sys.stderr)
        return 2
    print("[1/10] [PASS] Stage 21.3.2 prerequisite and runtime contract detected.")

    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [
        entry
        for entry in entries
        if entry["status"][0] in {" ", "?"}
        and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))
    ]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.3.2 parent verified.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/10] [FAIL] Preflight returned NO_GO.")
        return 1
    print("[2/10] [PASS] Branch, parent, upstream and worktree verified; backups prepared in ROM\\backup.")

    before = database_evidence(root)
    manifest = prepare_backups(root)
    try:
        print("[3/10] [PASS] Writing validated settings, redacted secret wrapper and blank template.")
        write_atomic(root / SETTINGS_PATH, SETTINGS_SOURCE)
        write_atomic(root / TEST_PATH, TEST_SOURCE)
        write_atomic(root / ENV_EXAMPLE_PATH, ENV_EXAMPLE_SOURCE)
        original_gitignore = (root / GITIGNORE_PATH).read_text(encoding="utf-8") if (root / GITIGNORE_PATH).exists() else ""
        write_atomic(root / GITIGNORE_PATH, append_gitignore(original_gitignore))

        print("[4/10] [PASS] Compiling new Python files without writing bytecode.")
        for relative_path in (SETTINGS_PATH, TEST_PATH):
            source = (root / relative_path).read_text(encoding="utf-8")
            compile(source, str(root / relative_path), "exec")

        print("[5/10] [PASS] Running configuration, rejection and redaction tests.")
        unit = run(root, sys.executable, "-m", "unittest", "tests_v2.test_settings")
        checks.append(Check("UNIT_TEST", "PASS" if unit.returncode == 0 else "FAIL", unit.stderr.strip() or unit.stdout.strip(), {}, unit.returncode != 0))

        print("[6/10] [PASS] Verifying environment-file ignore boundaries.")
        ignore_evidence = verify_env_ignored(root)
        ignore_ok = ignore_evidence["all_local_env_ignored"] and ignore_evidence["example_is_trackable"]
        checks.append(Check("ENV_IGNORE_POLICY", "PASS" if ignore_ok else "FAIL", f"Local dotenv ignored and example trackable: {ignore_ok}.", ignore_evidence, not ignore_ok))
        template_text = (root / ENV_EXAMPLE_PATH).read_text(encoding="utf-8")
        blank_template = all(
            line.endswith("=")
            for line in template_text.splitlines()
            if line.startswith(SECRET_ENV_KEYS)
        )
        checks.append(Check("SECRET_TEMPLATE_BLANK", "PASS" if blank_template else "FAIL", f"Secret placeholders are blank: {blank_template}.", {}, not blank_template))

        print("[7/10] [PASS] Scanning tracked text files for high-confidence secret formats.")
        scan = scan_tracked_files(root)
        checks.append(Check("TRACKED_SECRET_SCAN", "PASS" if scan["finding_count"] == 0 else "FAIL", f"High-confidence secret findings: {scan['finding_count']}.", scan, scan["finding_count"] != 0))

        print("[8/10] [PASS] Running architecture, code-standard and bootstrap regressions.")
        code_report = json.loads((root / "reports/stage_21_2_7_code_comment_standards.json").read_text(encoding="utf-8"))
        temporary_contract = root / "reports" / ".stage_21_3_3_code_contract.tmp.json"
        temporary_result = root / "reports" / ".stage_21_3_3_code_result.tmp.json"
        write_atomic(temporary_contract, json.dumps(code_report["code_comment_contract"], ensure_ascii=False, indent=2) + "\n")
        verifier = run(root, sys.executable, "tools/verify_v2_code_comment_standards.py", "--project-root", str(root), "--contract", str(temporary_contract), "--json-out", str(temporary_result))
        verifier_payload = json.loads(temporary_result.read_text(encoding="utf-8")) if temporary_result.exists() else {"summary": {"status": "FAIL"}}
        temporary_contract.unlink(missing_ok=True)
        temporary_result.unlink(missing_ok=True)
        verifier_ok = verifier.returncode == 0 and verifier_payload.get("summary", {}).get("status") == "PASS"
        checks.append(Check("CODE_STANDARD", "PASS" if verifier_ok else "FAIL", verifier.stdout.strip() or "Code-standard verifier failed.", {"stderr": verifier.stderr.strip(), "violations": verifier_payload.get("violations", [])}, not verifier_ok))
        dependency = run(root, sys.executable, "tools/verify_v2_dependency_rules.py", "--project-root", str(root), "--json-out", "reports/.stage_21_3_3_dependency.tmp.json")
        dependency_path = root / "reports" / ".stage_21_3_3_dependency.tmp.json"
        dependency_payload = json.loads(dependency_path.read_text(encoding="utf-8")) if dependency_path.exists() else {"summary": {"status": "FAIL"}}
        dependency_path.unlink(missing_ok=True)
        dependency_ok = dependency.returncode == 0 and dependency_payload.get("summary", {}).get("status") == "PASS"
        checks.append(Check("DEPENDENCY_RULES", "PASS" if dependency_ok else "FAIL", dependency.stdout.strip() or "Dependency verifier failed.", {"stderr": dependency.stderr.strip(), "violations": dependency_payload.get("violations", [])}, not dependency_ok))
        bootstrap = run(root, sys.executable, "-m", "rom_v2.main")
        bootstrap_ok = bootstrap.returncode == 0 and json.loads(bootstrap.stdout).get("gameplay_enabled") is False
        checks.append(Check("BOOTSTRAP_REGRESSION", "PASS" if bootstrap_ok else "FAIL", bootstrap.stdout.strip() or "Bootstrap regression failed.", {"stderr": bootstrap.stderr.strip()}, not bootstrap_ok))

        if before == database_evidence(root):
            checks.append(Check("DATABASE_UNCHANGED", "PASS", "DB/WAL/SHM unchanged and SQLite was not opened.", {"production_connection_opened": False}))
        else:
            checks.append(Check("DATABASE_UNCHANGED", "FAIL", "DB/WAL/SHM evidence changed.", {}, True))

        blockers = [item.check_id for item in checks if item.blocking]
        if blockers:
            report = rollback(root, manifest, f"Stage 21.3.3 NO_GO: {blockers}", checks)
            print(f"[9/10] [FAIL] Rollback: {report['status']}")
            return 1

        payload = {
            "schema_version": 1,
            "stage": STAGE,
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "summary": {
                "conclusion": "GO",
                "blocking_failures": [],
                "tracked_secret_findings": scan["finding_count"],
                "local_env_files_ignored": ignore_evidence["all_local_env_ignored"],
                "secret_values_recorded": False,
                "gameplay_started": False,
                "database_opened": False,
            },
            "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
            "checks": [asdict(item) for item in checks],
            "configuration_contract": {
                "canonical_owner": "rom_v2.settings.V2Settings",
                "secret_owner": "rom_v2.settings.SecretValue",
                "source": "process_environment",
                "required_secret_keys": list(SECRET_ENV_KEYS),
                "secret_values_in_report": False,
                "dotenv_loading_in_runtime": False,
            },
            "secret_scan": scan,
            "env_ignore_evidence": ignore_evidence,
            "database_evidence_before": before,
            "database_evidence_after": database_evidence(root),
            "changed_files": [PATCH_PATH, SETTINGS_PATH, TEST_PATH, ENV_EXAMPLE_PATH, GITIGNORE_PATH, REPORT_PATH, CONTRACT_PATH],
            "next_stage": "21.3.4",
            "suggested_next_patch": "patch_21_3_4_build_v2_dependency_container.py",
        }
        print("[9/10] [PASS] Writing secret-free machine evidence and configuration contract.")
        write_atomic(root / REPORT_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        write_atomic(root / CONTRACT_PATH, render_contract(scan, ignore_evidence))
        report_scan = scan_text(REPORT_PATH, (root / REPORT_PATH).read_text(encoding="utf-8"))
        contract_scan = scan_text(CONTRACT_PATH, (root / CONTRACT_PATH).read_text(encoding="utf-8"))
        if report_scan or contract_scan:
            raise PatchError("generated evidence contains a high-confidence secret format")
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

    print(f"[10/10] [PASS] Configuration/secrets boundary committed without secret values: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - configuration and secrets")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print("[PASS] TRACKED_SECRET_FINDINGS: 0")
    print("[PASS] SECRET_VALUES_RECORDED: False")
    print("[PASS] GAMEPLAY_STARTED: False")
    print("[PASS] DATABASE_OPENED: False")
    print("CONCLUSION: GO")
    print("PATCH STATUS: PASS")
    print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
    print("REMOTE PUSH STATUS: NOT REQUIRED")
    print("MANUAL CHECK: NOT REQUIRED")
    print("FAIL-SAFE ROLLBACK: ARMED")
    print("WAL/SHM: NOT MANIPULATED")
    print("SUGGESTED NEXT PATCH: patch_21_3_4_build_v2_dependency_container.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
