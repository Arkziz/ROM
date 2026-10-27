#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "rom_v2/domain/events/__init__.py",
    "rom_v2/domain/events/schedule.py",
    "rom_v2/domain/events/rewards.py",
    "rom_v2/domain/events/service.py",
    "tests/unit/events/test_event_schedules_rewards.py",
)


def main() -> int:
    for relative in FILES:
        if not (ROOT / relative).is_file():
            raise SystemExit(f"FAIL: missing {relative}")
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "tests.unit.events.test_event_schedules_rewards", "-v"],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)
    print("PASS: Stage 21.14.2c API-ready event schedules/rewards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
