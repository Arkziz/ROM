#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime
import re

ROOT = Path(__file__).resolve().parents[1]

DB_FILE = ROOT / "db.py"
BACKUP_DIR = ROOT / "backup"

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

REPORT = (
    BACKUP_DIR /
    f"INVENTORY_FACADE_LOCATOR_{STAMP}.txt"
)

TARGETS = [
    "get_inventory_detailed",
    "get_item_by_inventory_id",
    "get_item_by_inventory_id_full",
    "get_inventory_entry",
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

        start = max(0, m.start() - 120)
        end = min(len(text), m.start() + 220)

        log("")
        log(f"#{idx} line={line}")
        log("-" * 40)
        log(text[start:end])

REPORT.write_text(
    "\n".join(out),
    encoding="utf-8"
)

print()
print(REPORT)