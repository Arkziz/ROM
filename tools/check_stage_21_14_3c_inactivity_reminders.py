#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "rom_v2/domain/inactivity_reminders/__init__.py",
    "rom_v2/domain/inactivity_reminders/model.py",
    "rom_v2/domain/inactivity_reminders/service.py",
    "tests/unit/inactivity_reminders/test_inactivity_reminders.py",
)


def main() -> int:
    for relative in FILES:
        if not (ROOT / relative).is_file():
            raise SystemExit(f"FAIL: missing {relative}")
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "tests.unit.inactivity_reminders.test_inactivity_reminders", "-v"],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode:
        return completed.returncode
    print("PASS: Stage 21.14.3c API-ready inactivity reminders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
