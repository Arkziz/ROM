#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ROM 9.0.12i2 AUDIT PATCH

SAFE PATCH
- creates db.py backup
- validates cleanup readiness markers
- validates Player/Energy/Regen wrappers
- writes audit report

NO db.py modifications
"""

from pathlib import Path
from datetime import datetime
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]

DB_FILE = ROOT / "db.py"
BACKUP_DIR = ROOT / "backup"

AUDIT_REPORT = (
    BACKUP_DIR /
    f"DB_AUDIT_9_0_12i2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
)


REQUIRED_MARKERS = [
    "ROM 9.0.12b CHARACTER SYSTEM REAL IMPLEMENTATION V1",
    "ROM 9.0.2 PLAYER SYSTEM FACADE WRAPPERS V1",
    "ROM 9.0.12c1 PLAYER PROGRESSION REAL IMPLEMENTATION WRAPPERS V1",
    "ROM 9.0.12e1 ENERGY SYSTEM REAL IMPLEMENTATION WRAPPERS V2",
    "ROM 9.0.12e2 REGEN SYSTEM REAL IMPLEMENTATION WRAPPERS V2",
]


PLAYER_WRAPPERS = [
    "get_player_level",
    "get_wallet",
    "add_gold",
    "add_kill",
    "get_current_hp_raw",
    "get_current_hp",
    "set_current_hp",
]


ENERGY_WRAPPERS = [
    "init_energy_system",
    "get_user_energy",
    "consume_energy_for_hunt",
    "restore_energy_for_test",
    "get_users_for_energy_full_notification",
]


REGEN_WRAPPERS = [
    "init_hp_regen_system",
    "init_passive_regen_system",
    "process_passive_regeneration",
    "reset_hp_regen_timers_now",
    "apply_passive_hp_regen",
]


LEGACY_REFERENCES = [
    "_legacy_equipment_ro_v1_can_equip_item_by_class",
    "_legacy_equipment_ro_v1_can_equip_inventory_item_by_class",
    "_legacy_equipment_ro_v1_is_inventory_item_class_compatible",
]


def log(line=""):
    print(line)
    REPORT_LINES.append(line)


def backup_db():
    BACKUP_DIR.mkdir(exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_file = BACKUP_DIR / f"db_before_9_0_12i2_audit_{stamp}.py"

    shutil.copy2(DB_FILE, backup_file)

    log(f"✅ Backup created:")
    log(f"   {backup_file}")

    return backup_file


def count_defs(text: str):
    return len(
        re.findall(
            r"^def\s+[A-Za-z0-9_]+\(",
            text,
            flags=re.MULTILINE,
        )
    )


def find_duplicates(text: str):
    names = re.findall(
        r"^def\s+([A-Za-z0-9_]+)\(",
        text,
        flags=re.MULTILINE,
    )

    duplicates = {}

    for name in names:
        duplicates[name] = duplicates.get(name, 0) + 1

    return {
        k: v
        for k, v in duplicates.items()
        if v > 1
    }


def audit():
    text = DB_FILE.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    log("=" * 60)
    log("ROM 9.0.12i2 AUDIT")
    log("=" * 60)

    log()

    log(f"db.py size: {len(text):,} chars")
    log(f"function defs: {count_defs(text)}")

    log()
    log("=== MARKERS ===")

    for marker in REQUIRED_MARKERS:

        found = marker in text

        if found:
            log(f"✅ {marker}")
        else:
            log(f"❌ {marker}")

    log()
    log("=== PLAYER WRAPPERS ===")

    for fn in PLAYER_WRAPPERS:
        found = f"def {fn}(" in text

        log(
            f"{'✅' if found else '❌'} {fn}"
        )

    log()
    log("=== ENERGY WRAPPERS ===")

    for fn in ENERGY_WRAPPERS:
        found = f"def {fn}(" in text

        log(
            f"{'✅' if found else '❌'} {fn}"
        )

    log()
    log("=== REGEN WRAPPERS ===")

    for fn in REGEN_WRAPPERS:
        found = f"def {fn}(" in text

        log(
            f"{'✅' if found else '❌'} {fn}"
        )

    log()
    log("=== LEGACY REFERENCES ===")

    for ref in LEGACY_REFERENCES:
        found = ref in text

        log(
            f"{'✅' if found else '❌'} {ref}"
        )

    log()
    log("=== DUPLICATES ===")

    duplicates = find_duplicates(text)

    log(f"duplicate names: {len(duplicates)}")

    top = sorted(
        duplicates.items(),
        key=lambda x: x[1],
        reverse=True
    )[:30]

    for name, qty in top:
        log(f"  {name}: {qty}")

    log()
    log("✅ AUDIT COMPLETED")


REPORT_LINES = []


def main():
    if not DB_FILE.exists():
        print("❌ db.py not found")
        return

    backup_db()

    audit()

    AUDIT_REPORT.write_text(
        "\n".join(REPORT_LINES),
        encoding="utf-8"
    )

    print()
    print(f"📝 Report:")
    print(AUDIT_REPORT)


if __name__ == "__main__":
    main()