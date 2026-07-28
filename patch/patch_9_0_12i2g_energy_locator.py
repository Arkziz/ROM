#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime
import re

ROOT = Path(__file__).resolve().parents[1]

DB_FILE = ROOT / "db.py"

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

REPORT = ROOT / "backup" / f"ENERGY_LOCATOR_{STAMP}.txt"

TARGETS = [
    "init_energy_system",
    "get_user_energy",
    "consume_energy_for_hunt",
    "restore_energy_for_test",
    "get_users_for_energy_full_notification",
]

out = []

def log(x=""):
    print(x)
    out.append(x)

text = DB_FILE.read_text(
    encoding="utf-8",
    errors="ignore"
)

for target in TARGETS:

    log("=" * 70)
    log(target)
    log("=" * 70)

    pattern = re.compile(
        rf"^def\s+{re.escape(target)}\(",
        re.MULTILINE
    )

    matches = list(pattern.finditer(text))

    log(f"count={len(matches)}")

    for idx, m in enumerate(matches, start=1):

        line = text[:m.start()].count("\n") + 1

        start = max(0, m.start() - 150)
        end = min(len(text), m.start() + 250)

        snippet = text[start:end]

        log("")
        log(f"#{idx} line={line}")
        log("-" * 30)
        log(snippet[:200])

REPORT.write_text(
    "\n".join(out),
    encoding="utf-8"
)

print()
print(REPORT)