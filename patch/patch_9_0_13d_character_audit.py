#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]

DB_FILE = ROOT / "db.py"

BACKUP_DIR = ROOT / "backup"
BACKUP_DIR.mkdir(exist_ok=True)

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

BACKUP_FILE = (
    BACKUP_DIR /
    f"db_before_character_audit_{STAMP}.py"
)

REPORT_FILE = (
    BACKUP_DIR /
    f"CHARACTER_AUDIT_{STAMP}.txt"
)

TARGETS = [
    "get_character_name",
    "get_character_class",
    "get_character_class_display",
    "get_character_resource_type",
    "normalize_character_name",
    "validate_character_name",
    "set_character_class",
]

out = []

def log(x=""):
    print(x)
    out.append(x)

shutil.copy2(DB_FILE, BACKUP_FILE)

log("✅ Backup created")
log(str(BACKUP_FILE))
log()

text = DB_FILE.read_text(
    encoding="utf-8",
    errors="ignore"
)

for fn in TARGETS:

    log("=" * 60)
    log(fn)
    log("=" * 60)

    pattern = re.compile(
        rf"^def\s+{re.escape(fn)}\(",
        re.MULTILINE
    )

    matches = list(pattern.finditer(text))

    log(f"definitions={len(matches)}")

    for idx, m in enumerate(matches, start=1):

        line = text[:m.start()].count("\n") + 1

        log(f"#{idx} line={line}")

    log()

REPORT_FILE.write_text(
    "\n".join(out),
    encoding="utf-8"
)

print()
print(REPORT_FILE)