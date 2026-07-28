#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ROM 9.0.13

PRE-CLEANUP AUDIT

SAFE PATCH
NO MODIFICATIONS

Створює:

backup/PRE_CLEANUP_AUDIT_*.txt

Показує:
- definitions
- duplicate defs
- duplicate ranking
- cleanup candidates
"""

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
    f"db_before_precleanup_audit_{STAMP}.py"
)

REPORT_FILE = (
    BACKUP_DIR /
    f"PRE_CLEANUP_AUDIT_{STAMP}.txt"
)

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


def extract_defs(text):

    result = []

    for match in re.finditer(
        r"^def\s+([a-zA-Z0-9_]+)\(",
        text,
        re.MULTILINE
    ):

        line = (
            text[:match.start()]
            .count("\n")
        ) + 1

        result.append(
            (
                match.group(1),
                line
            )
        )

    return result


def main():

    if not DB_FILE.exists():
        print("❌ db.py not found")
        return

    backup()

    text = load_text()

    defs = extract_defs(text)

    log("=" * 70)
    log("ROM 9.0.13 PRE-CLEANUP AUDIT")
    log("=" * 70)
    log()

    log(f"definitions: {len(defs)}")
    log()

    names = [x[0] for x in defs]

    counter = Counter(names)

    duplicates = {
        k: v
        for k, v in counter.items()
        if v > 1
    }

    log(f"duplicate names: {len(duplicates)}")
    log()

    log("=" * 70)
    log("TOP DUPLICATES")
    log("=" * 70)

    for name, count in sorted(
        duplicates.items(),
        key=lambda x: x[1],
        reverse=True
    ):

        log(
            f"{name:<45} {count}"
        )

    log()
    log("=" * 70)
    log("CANDIDATE GROUPS")
    log("=" * 70)

    groups = {
        "PLAYER": [
            "get_player_level",
            "get_wallet",
            "add_gold",
            "add_kill",
            "add_exp",
            "get_user_progress",
        ],
        "ENERGY": [
            "init_energy_system",
            "get_user_energy",
            "consume_energy_for_hunt",
            "restore_energy_for_test",
            "get_users_for_energy_full_notification",
        ],
        "REGEN": [
            "init_hp_regen_system",
            "process_passive_regeneration",
            "apply_passive_hp_regen",
            "reset_hp_regen_timers_now",
        ],
        "EQUIPMENT": [
            "get_inventory_detailed",
            "get_item_by_inventory_id",
            "get_item_by_inventory_id_full",
            "get_inventory_entry",
            "get_weapon_damage_by_inventory_id",
            "create_generated_equipment_item",
            "buy_common_equipment_from_trader",
            "repair_equipped_item",
            "repair_all_equipped",
        ],
    }

    for group_name, functions in groups.items():

        log()
        log(f"[{group_name}]")

        for fn in functions:

            count = counter.get(fn, 0)

            if count > 1:

                log(
                    f"  {fn:<45} "
                    f"duplicates={count}"
                )

    log()
    log("=" * 70)
    log("DUPLICATE LOCATIONS")
    log("=" * 70)

    for name, count in sorted(
        duplicates.items(),
        key=lambda x: x[1],
        reverse=True
    ):

        locations = [
            line
            for fn, line in defs
            if fn == name
        ]

        log()
        log(f"{name}")

        for idx, line in enumerate(
            locations,
            start=1
        ):
            log(
                f"  #{idx} line {line}"
            )

    REPORT_FILE.write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print()
    print("✅ PRE-CLEANUP AUDIT DONE")
    print(REPORT_FILE)


if __name__ == "__main__":
    main()