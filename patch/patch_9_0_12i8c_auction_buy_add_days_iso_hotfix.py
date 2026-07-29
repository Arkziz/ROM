#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i8c: fix undefined add_days_iso in Auction purchase flow."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.12i8c"
OLD = "delete_after = add_days_iso(now, AUCTION_UNCLAIMED_RETENTION_DAYS)"
NEW = "delete_after = _auction_plus_days_iso_v2(now, AUCTION_UNCLAIMED_RETENTION_DAYS)"
TESTS = (
    "smoke_test_auction_lifecycle_contracts.py",
    "smoke_test_rom_core.py",
    "check_imports.py",
)


def fail(message):
    print(f"❌ {message}")
    raise SystemExit(1)


def find_root():
    here = Path(__file__).resolve()
    for root in (here.parent.parent, Path.cwd(), Path.cwd().parent):
        root = root.resolve()
        if (
            (root / "db.py").is_file()
            and (root / "systems" / "auction_house_system.py").is_file()
            and (root / "tools" / "db_cleanup_readiness.py").is_file()
        ):
            return root
    fail("Не знайдено корінь ROM.")


def run_checked(root, path, label):
    result = subprocess.run([sys.executable, str(path)], cwd=root, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{label} exit code {result.returncode}")


def called_names(tree):
    names = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            names.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            names.append(node.func.attr)
    return names


def main():
    root = find_root()
    target = root / "systems" / "auction_house_system.py"
    tools = root / "tools"
    readiness = tools / "db_cleanup_readiness.py"

    for test_name in TESTS:
        if not (tools / test_name).is_file():
            fail(f"Відсутній tools/{test_name}.")

    source = target.read_text(encoding="utf-8-sig")

    if OLD not in source and NEW in source:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
        for test_name in TESTS:
            run_checked(root, tools / test_name, test_name)
        return

    old_count = source.count(OLD)
    if old_count != 1:
        fail(f"Неочікувана кількість проблемних викликів add_days_iso: {old_count}, очікувалося 1.")
    if "def _auction_plus_days_iso_v2(" not in source:
        fail("Не знайдено наявний helper _auction_plus_days_iso_v2().")

    updated = source.replace(OLD, NEW, 1)
    tree = ast.parse(updated, filename=str(target))
    calls = called_names(tree)
    if "add_days_iso" in calls:
        fail("Після заміни залишився виклик невизначеного add_days_iso().")
    if "_auction_plus_days_iso_v2" not in calls:
        fail("Після заміни не знайдено виклик _auction_plus_days_iso_v2().")

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"systems_auction_house_system.py_{PATCH_ID}_{stamp}.bak"
    shutil.copy2(target, backup)

    temp = target.with_name(".auction_house_system.i8c.tmp")
    try:
        temp.write_text(updated, encoding="utf-8")
        os.replace(temp, target)
        py_compile.compile(str(target), doraise=True)

        for test_name in TESTS:
            run_checked(root, tools / test_name, test_name)

        result = subprocess.run(
            [sys.executable, str(readiness)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        print(result.stdout, end="")
        if result.returncode != 0:
            raise RuntimeError(f"readiness exit code {result.returncode}")
        for expected in (
            "definitions: 353",
            "duplicates: 2",
            "legacy_refs: 0",
            "unsafe_delete: 0",
            "maybe_cleanup_later: 2",
        ):
            if expected not in result.stdout:
                raise RuntimeError(f"readiness не містить: {expected}")

    except Exception as exc:
        shutil.copy2(backup, target)
        if temp.exists():
            temp.unlink()
        fail(f"Перевірка не пройдена; auction_house_system.py відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ Виправлено undefined name add_days_iso у purchase flow.")
    print("✅ Використано наявний helper _auction_plus_days_iso_v2.")
    print("✅ Статус активного лота та транзакційний захист не змінені.")
    print("Резервні копії:")
    print(f"   {backup.relative_to(root)}")
    print("Перевірки:")
    print("   python -m py_compile ./systems/auction_house_system.py")
    for test_name in TESTS:
        print(f"   python ./tools/{test_name}")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
