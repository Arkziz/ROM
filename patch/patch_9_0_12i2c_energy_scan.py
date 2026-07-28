#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ROM 9.0.12i2c

ENERGY DEPENDENCY SCAN

SAFE PATCH
NO MODIFICATIONS

Сканує проєкт на використання Energy API.
"""

from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]

BACKUP_DIR = ROOT / "backup"
BACKUP_DIR.mkdir(exist_ok=True)

STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

REPORT_FILE = (
    BACKUP_DIR /
    f"ENERGY_SCAN_9_0_12i2c_{STAMP}.txt"
)

DB_FILE = ROOT / "db.py"

SEARCH_TERMS = [
    "_energy_system_v1",
    "init_energy_system(",
    "get_user_energy(",
    "consume_energy_for_hunt(",
    "restore_energy_for_test(",
    "get_users_for_energy_full_notification(",
]

SEARCH_DIRS = [
    ROOT / "handlers",
    ROOT / "systems",
    ROOT / "tools",
]


lines = []


def log(text=""):
    print(text)
    lines.append(text)


def backup():
    target = (
        BACKUP_DIR /
        f"db_before_energy_scan_{STAMP}.py"
    )

    shutil.copy2(DB_FILE, target)

    log("✅ Backup created")
    log(str(target))
    log()


def scan_file(file_path, term):
    results = []

    try:
        text = file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except Exception:
        return results

    for lineno, line in enumerate(
        text.splitlines(),
        start=1
    ):
        if term in line:
            results.append(
                (
                    lineno,
                    line.strip()
                )
            )

    return results


def main():
    backup()

    log("=" * 70)
    log("ROM 9.0.12i2c")
    log("ENERGY DEPENDENCY SCAN")
    log("=" * 70)
    log()

    total_hits = 0

    for term in SEARCH_TERMS:

        log("-" * 70)
        log(f"SEARCH: {term}")
        log("-" * 70)

        found_any = False

        for directory in SEARCH_DIRS:

            if not directory.exists():
                continue

            for file_path in directory.rglob("*.py"):

                matches = scan_file(
                    file_path,
                    term
                )

                if not matches:
                    continue

                found_any = True

                rel = file_path.relative_to(ROOT)

                log()
                log(f"{rel}")

                for lineno, content in matches:
                    total_hits += 1

                    log(
                        f"  L{lineno}: {content}"
                    )

        if not found_any:
            log("NO RESULTS")

        log()

    log("=" * 70)
    log(f"TOTAL HITS: {total_hits}")
    log("=" * 70)

    REPORT_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print()
    print("✅ Scan completed")
    print(REPORT_FILE)


if __name__ == "__main__":
    main()