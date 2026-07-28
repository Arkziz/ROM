#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime
import re

ROOT = Path(__file__).resolve().parents[1]

DB_FILE = ROOT / "db.py"

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

REPORT = ROOT / "backup" / f"PLAYER_LOCATOR_{STAMP}.txt"

TARGETS = [
    "get_player_level",
    "get_wallet",
    "add_gold",
    "add_kill",
    "get_current_hp_raw",
    "get_current_hp",
    "set_current_hp",
]

lines_out = []

def log(x=""):
    print(x)
    lines_out.append(x)

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

        log(f"#{idx} line={line}")

    log()

REPORT.write_text(
    "\n".join(lines_out),
    encoding="utf-8"
)

print()
print(REPORT)