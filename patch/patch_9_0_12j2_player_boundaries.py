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
    f"db_before_player_boundaries_{STAMP}.py"
)

REPORT_FILE = (
    BACKUP_DIR /
    f"PLAYER_BOUNDARIES_{STAMP}.txt"
)

TARGETS = [
    "get_player_level",
    "add_gold",
    "add_kill",
    "get_wallet",
]

report_lines = []


def log(text=""):
    print(text)
    report_lines.append(text)


def backup():
    shutil.copy2(DB_FILE, BACKUP_FILE)

    log("✅ Backup created")
    log(str(BACKUP_FILE))
    log("")


def find_defs(text, fn_name):

    pattern = re.compile(
        rf"^def\s+{re.escape(fn_name)}\(",
        re.MULTILINE
    )

    result = []

    for match in pattern.finditer(text):

        line = (
            text[:match.start()]
            .count("\n")
        ) + 1

        result.append(line)

    return result


def main():

    if not DB_FILE.exists():
        print("❌ db.py not found")
        return

    backup()

    text = DB_FILE.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    log("=" * 70)
    log("ROM 9.0.12j2")
    log("PLAYER BOUNDARY REPORT")
    log("=" * 70)
    log("")

    first_defs = []

    for fn in TARGETS:

        defs = find_defs(text, fn)

        log(fn)

        for idx, line in enumerate(defs, start=1):

            log(
                f"  #{idx} line {line}"
            )

        if defs:
            first_defs.append(defs[0])

        log("")

    if first_defs:

        block_start = min(first_defs)

        block_end = max(first_defs) + 50

        log("=" * 70)
        log("FIRST LEGACY PLAYER BLOCK")
        log("=" * 70)

        log(
            f"START LINE : {block_start}"
        )

        log(
            f"END LINE   : {block_end}"
        )

        log(
            f"SIZE       : {block_end - block_start}"
        )

    REPORT_FILE.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    print()
    print("✅ Report saved")
    print(REPORT_FILE)


if __name__ == "__main__":
    main()