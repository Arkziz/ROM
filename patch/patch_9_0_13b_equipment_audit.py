#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime
import shutil
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

DB_FILE = ROOT / "db.py"

BACKUP_DIR = ROOT / "backup"
BACKUP_DIR.mkdir(exist_ok=True)

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

BACKUP_FILE = (
    BACKUP_DIR /
    f"db_before_equipment_audit_{STAMP}.py"
)

REPORT_FILE = (
    BACKUP_DIR /
    f"EQUIPMENT_AUDIT_{STAMP}.txt"
)

TARGETS = [
    "get_inventory_detailed",
    "get_item_by_inventory_id",
    "get_item_by_inventory_id_full",
    "get_inventory_entry",
    "get_weapon_damage_by_inventory_id",
    "create_generated_equipment_item",
    "buy_common_equipment_from_trader",
    "repair_equipped_item",
    "repair_all_equipped",
]

report = []


def log(text=""):
    print(text)
    report.append(text)


def backup():
    shutil.copy2(DB_FILE, BACKUP_FILE)

    log("✅ Backup created")
    log(str(BACKUP_FILE))
    log("")


def load_text():

    return DB_FILE.read_text(
        encoding="utf-8",
        errors="ignore"
    )


def find_defs(text, fn_name):

    result = []

    pattern = re.compile(
        rf"^def\s+{re.escape(fn_name)}\(",
        re.MULTILINE
    )

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

    text = load_text()

    log("=" * 70)
    log("ROM 9.0.13b EQUIPMENT AUDIT")
    log("=" * 70)
    log("")

    duplicate_total = 0

    for fn in TARGETS:

        defs = find_defs(text, fn)

        duplicate_total += max(
            0,
            len(defs) - 1
        )

        log(fn)

        log(
            f"definitions = {len(defs)}"
        )

        for idx, line in enumerate(
            defs,
            start=1
        ):

            log(
                f"  #{idx} line {line}"
            )

        log("")

    log("=" * 70)
    log("SUMMARY")
    log("=" * 70)

    log(
        f"equipment duplicate count = {duplicate_total}"
    )

    REPORT_FILE.write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print()
    print("✅ Equipment audit complete")
    print(REPORT_FILE)


if __name__ == "__main__":
    main()