#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ROM 9.0.12i2f

ENERGY BOUNDARY MAPPER

SAFE PATCH
NO MODIFICATIONS

Мета:
- знайти всі Energy блоки в db.py
- показати точні номери рядків
- створити backup
- НЕ змінювати код
"""

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
    f"db_before_energy_boundaries_{STAMP}.py"
)

REPORT_FILE = (
    BACKUP_DIR /
    f"ENERGY_BOUNDARIES_9_0_12i2f_{STAMP}.txt"
)

MARKERS = [
    "## ✅ ENERGY SYSTEM",
    "## ✅ PASSIVE HP REGEN SYSTEM",
    "## ✅ OVERRIDE: SAFE ENERGY INIT + NEW USER ENERGY FIX",
    "## ✅ ROM 9.0.12e1 ENERGY SYSTEM REAL IMPLEMENTATION WRAPPERS V2",
]

lines_out = []


def log(text=""):
    print(text)
    lines_out.append(text)


def backup():
    shutil.copy2(DB_FILE, BACKUP_FILE)

    log("✅ Backup created")
    log(str(BACKUP_FILE))
    log()


def find_markers(lines):
    results = {}

    for marker in MARKERS:

        for idx, line in enumerate(lines, start=1):

            if marker in line:
                results[marker] = idx
                break

    return results


def main():

    if not DB_FILE.exists():
        print("❌ db.py not found")
        return

    backup()

    text = DB_FILE.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    lines = text.splitlines()

    markers = find_markers(lines)

    log("=" * 70)
    log("ROM 9.0.12i2f")
    log("ENERGY BOUNDARY REPORT")
    log("=" * 70)
    log()

    for marker in MARKERS:

        line_no = markers.get(marker)

        if line_no:
            log(f"✅ line {line_no:<6} {marker}")
        else:
            log(f"❌ NOT FOUND: {marker}")

    log()
    log("=" * 70)

    energy_start = markers.get(
        "## ✅ ENERGY SYSTEM"
    )

    energy_end = markers.get(
        "## ✅ PASSIVE HP REGEN SYSTEM"
    )

    if energy_start and energy_end:

        block_size = energy_end - energy_start

        log("ENERGY LEGACY BLOCK")

        log(
            f"START : line {energy_start}"
        )

        log(
            f"END   : line {energy_end - 1}"
        )

        log(
            f"LINES : {block_size}"
        )

    else:
        log(
            "Unable to calculate "
            "legacy energy block boundaries."
        )

    log()
    log("=" * 70)

    wrapper_line = markers.get(
        "## ✅ ROM 9.0.12e1 ENERGY SYSTEM REAL IMPLEMENTATION WRAPPERS V2"
    )

    if wrapper_line:

        log(
            f"FINAL ENERGY WRAPPERS BEGIN AT LINE {wrapper_line}"
        )

    REPORT_FILE.write_text(
        "\n".join(lines_out),
        encoding="utf-8"
    )

    print()
    print("✅ Boundary report saved")
    print(REPORT_FILE)


if __name__ == "__main__":
    main()