#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ROM 9.0.12i2d

ENERGY RUNTIME CLEANUP

SAFE PATCH

Дія:
- створює backup systems/energy_system.py
- видаляє старі _energy_system_v1 wrappers
- НЕ чіпає db.py
"""

from pathlib import Path
from datetime import datetime
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]

ENERGY_FILE = ROOT / "systems" / "energy_system.py"

BACKUP_DIR = ROOT / "backup"
BACKUP_DIR.mkdir(exist_ok=True)

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

BACKUP_FILE = (
    BACKUP_DIR /
    f"energy_system_before_runtime_cleanup_{STAMP}.py"
)


def main():

    if not ENERGY_FILE.exists():
        print("❌ systems/energy_system.py not found")
        return

    shutil.copy2(
        ENERGY_FILE,
        BACKUP_FILE
    )

    print("✅ Backup created")
    print(BACKUP_FILE)

    text = ENERGY_FILE.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    pattern = re.compile(
        r"""
def\s+init_energy_system\(\*args,\s*\*\*kwargs\):\s*
\s*return\s+_energy_system_v1\(\)\.init_energy_system\(\*args,\s*\*\*kwargs\)\s*

def\s+get_user_energy\(\*args,\s*\*\*kwargs\):\s*
\s*return\s+_energy_system_v1\(\)\.get_user_energy\(\*args,\s*\*\*kwargs\)\s*
""",
        re.VERBOSE | re.MULTILINE
    )

    new_text, count = pattern.subn(
        "\n",
        text,
        count=1
    )

    if count == 0:
        print("⚠️ Runtime wrapper block not found")
        return

    ENERGY_FILE.write_text(
        new_text,
        encoding="utf-8"
    )

    print()
    print("✅ Removed legacy runtime wrappers")
    print("✅ systems/energy_system.py updated")
    print()
    print("NEXT:")
    print("python -m py_compile .\\systems\\energy_system.py")
    print("python tools\\smoke_test_energy_contracts.py")


if __name__ == "__main__":
    main()