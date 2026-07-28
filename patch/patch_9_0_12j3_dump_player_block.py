#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

DB_FILE = ROOT / "db.py"
BACKUP_DIR = ROOT / "backup"

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

OUT_FILE = (
    BACKUP_DIR /
    f"PLAYER_BLOCK_DUMP_{STAMP}.txt"
)

START_LINE = 850
END_LINE = 1500

text = DB_FILE.read_text(
    encoding="utf-8",
    errors="ignore"
)

lines = text.splitlines()

block = lines[
    START_LINE - 1:
    END_LINE
]

OUT_FILE.write_text(
    "\n".join(block),
    encoding="utf-8"
)

print("✅ Dump saved")
print(OUT_FILE)