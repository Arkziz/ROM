#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]

DB_FILE = ROOT / "db.py"

BACKUP_DIR = ROOT / "backup"
BACKUP_DIR.mkdir(exist_ok=True)

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

BACKUP_FILE = (
    BACKUP_DIR /
    f"db_before_energy_cleanup_{STAMP}.py"
)


START_MARKER = """
def init_energy_system():
"""

END_MARKER = """
# ==============================
# ✅ PASSIVE HP REGEN SYSTEM
# ==============================
"""


def main():

    if not DB_FILE.exists():
        print("❌ db.py not found")
        return

    shutil.copy2(DB_FILE, BACKUP_FILE)

    print("✅ Backup created")
    print(BACKUP_FILE)

    text = DB_FILE.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    start_pos = text.find(START_MARKER)

    if start_pos < 0:
        print("❌ Energy block start not found")
        return

    end_pos = text.find(
        END_MARKER,
        start_pos
    )

    if end_pos < 0:
        print("❌ Energy block end not found")
        return

    removed_size = end_pos - start_pos

    new_text = (
        text[:start_pos]
        + "\n\n"
        + text[end_pos:]
    )

    DB_FILE.write_text(
        new_text,
        encoding="utf-8"
    )

    print()
    print("✅ Legacy Energy block removed")
    print(f"Removed chars: {removed_size}")
    print()
    print("NEXT:")
    print("python -m py_compile .\\db.py")
    print("python tools\\smoke_test_energy_contracts.py")
    print("python tools\\db_cleanup_readiness.py")


if __name__ == "__main__":
    main()