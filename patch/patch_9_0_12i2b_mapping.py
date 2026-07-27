#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ROM 9.0.12i2b

LEGACY BLOCK MAPPING

SAFE PATCH
NO MODIFICATIONS

Creates:

backup/DB_MAPPING_9_0_12i2b_*.txt
"""

from pathlib import Path
from datetime import datetime
import shutil
import re


ROOT = Path(__file__).resolve().parents[1]

DB_FILE = ROOT / "db.py"
BACKUP_DIR = ROOT / "backup"

BACKUP_DIR.mkdir(exist_ok=True)

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

REPORT = (
    BACKUP_DIR /
    f"DB_MAPPING_9_0_12i2b_{STAMP}.txt"
)


TARGETS = [
    "get_player_level",
    "get_wallet",
    "add_gold",
    "add_kill",
    "get_current_hp_raw",
    "get_current_hp",
    "set_current_hp",

    "init_energy_system",
    "get_user_energy",
    "consume_energy_for_hunt",
    "restore_energy_for_test",
    "get_users_for_energy_full_notification",

    "init_hp_regen_system",
    "init_passive_regen_system",
    "process_passive_regeneration",
    "reset_hp_regen_timers_now",
    "apply_passive_hp_regen",
]


LINES = []


def log(text=""):
    print(text)
    LINES.append(text)


def backup():
    target = (
        BACKUP_DIR /
        f"db_before_mapping_{STAMP}.py"
    )

    shutil.copy2(DB_FILE, target)

    log("✅ Backup created")
    log(str(target))
    log()

    return target


def find_definitions(text, fn_name):
    results = []

    pattern = re.compile(
        rf"^def\s+{re.escape(fn_name)}\(",
        re.MULTILINE,
    )

    for m in pattern.finditer(text):
        line = text[:m.start()].count("\n") + 1
        results.append(line)

    return results


def section_type(line):
    if line < 12000:
        return "LEGACY"

    if line < 12600:
        return "TRANSITION"

    return "FACADE/WRAPPER"


def main():
    if not DB_FILE.exists():
        print("db.py not found")
        return

    backup()

    text = DB_FILE.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    log("=" * 70)
    log("ROM 9.0.12i2b")
    log("LEGACY BLOCK MAPPING")
    log("=" * 70)
    log()

    cleanup_candidates = []

    for fn in TARGETS:

        lines = find_definitions(text, fn)

        log("-" * 70)
        log(fn)
        log("-" * 70)

        if not lines:
            log("NOT FOUND")
            log()
            continue

        log(f"Definitions: {len(lines)}")

        for idx, line in enumerate(lines, start=1):
            kind = section_type(line)

            log(
                f"  #{idx:<2} line={line:<6} [{kind}]"
            )

        if len(lines) >= 2:
            cleanup_candidates.append(fn)

        log()

    log("=" * 70)
    log("POTENTIAL CLEANUP CANDIDATES")
    log("=" * 70)

    for fn in cleanup_candidates:
        log(fn)

    REPORT.write_text(
        "\n".join(LINES),
        encoding="utf-8",
    )

    print()
    print("✅ Mapping completed")
    print(REPORT)


if __name__ == "__main__":
    main()