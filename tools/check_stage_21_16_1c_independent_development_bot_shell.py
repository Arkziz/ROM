"""Verifier for Stage 21.16.1c independent development bot shell."""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSPORT = ROOT / "rom_v2/infrastructure/telegram/bot_api.py"
FILES = [
    TRANSPORT,
    ROOT / "rom_v2/presentation/development_shell.py",
    ROOT / "rom_v2/app/development_bot.py",
    ROOT / "tests_v2/test_independent_development_bot_shell.py",
]
FORBIDDEN_TRANSPORT_IMPORT_PREFIXES = (
    "sqlite3", "rom_v2.infrastructure.persistence", "rom_v2.application", "rom_v2.domain"
)
FORBIDDEN_TRANSPORT_NAMES = {
    "Connection", "Repository", "UnitOfWork", "ConnectionFactory"
}


def main() -> int:
    errors: list[str] = []
    for path in FILES:
        if not path.is_file():
            errors.append(f"missing file: {path.relative_to(ROOT)}")
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as error:
            errors.append(f"syntax error: {path.relative_to(ROOT)}: {error}")
            continue
        if path == TRANSPORT:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    names = []
                if any(name == prefix or name.startswith(prefix + ".") for name in names for prefix in FORBIDDEN_TRANSPORT_IMPORT_PREFIXES):
                    errors.append("Telegram Bot API transport contains persistence coupling")
                if isinstance(node, ast.Name) and node.id in FORBIDDEN_TRANSPORT_NAMES:
                    errors.append("Telegram Bot API transport contains persistence coupling")
    if not errors:
        command = [sys.executable, "-m", "unittest", "tests_v2.test_independent_development_bot_shell"]
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if completed.returncode:
            errors.append(completed.stdout + completed.stderr)
    if errors:
        print("FAIL")
        for error in dict.fromkeys(errors):
            print(f"- {error.strip()}")
        return 1
    print("PASS")
    print("- Telegram transport is HTTP-only and persistence-independent")
    print("- V2 shell presentation is mutation-free")
    print("- allowlist and shell routing probes passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
