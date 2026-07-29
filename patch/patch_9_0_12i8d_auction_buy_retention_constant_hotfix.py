#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i8d: fix undefined Auction retention constant in purchase flow."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.12i8d"
OLD = "delete_after = _auction_plus_days_iso_v2(now, AUCTION_UNCLAIMED_RETENTION_DAYS)"
NEW = "delete_after = _auction_plus_days_iso_v2(now, AUCTION_UNCLAIMED_RETENTION_DAYS_V2)"
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

    if source.count(OLD) != 1:
        fail(f"Проблемний виклик знайдено {source.count(OLD)} разів, очікувалося 1.")
    if "AUCTION_UNCLAIMED_RETENTION_DAYS_V2 = 30" not in source:
        fail("Не знайдено визначення AUCTION_UNCLAIMED_RETENTION_DAYS_V2.")

    updated = source.replace(OLD, NEW, 1)
    tree = ast.parse(updated, filename=str(target))

    defined = set()
    loaded = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                defined.add(node.id)
            elif isinstance(node.ctx, ast.Load):
                loaded.add(node.id)

    if "AUCTION_UNCLAIMED_RETENTION_DAYS" in loaded and "AUCTION_UNCLAIMED_RETENTION_DAYS" not in defined:
        fail("Після зміни залишилося використання невизначеної старої retention-константи.")
    if "AUCTION_UNCLAIMED_RETENTION_DAYS_V2" not in defined:
        fail("V2 retention-константа не визначена після зміни.")

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"systems_auction_house_system.py_{PATCH_ID}_{stamp}.bak"
    shutil.copy2(target, backup)

    temp = target.with_name(".auction_house_system.i8d.tmp")
    try:
        temp.write_text(updated, encoding="utf-8")
        os.replace(temp, target)
        py_compile.compile(str(target), doraise=True)

        for test_name in TESTS:
            run_checked(root, tools / test_name, test_name)

        result = subprocess.run(
            [sys.executable, str(readiness)], cwd=root,
            text=True, capture_output=True, check=False,
        )
        print(result.stdout, end="")
        if result.returncode != 0:
            raise RuntimeError(f"readiness exit code {result.returncode}")
        for expected in (
            "definitions: 353", "duplicates: 2", "legacy_refs: 0",
            "unsafe_delete: 0", "maybe_cleanup_later: 2",
        ):
            if expected not in result.stdout:
                raise RuntimeError(f"readiness не містить: {expected}")

    except Exception as exc:
        shutil.copy2(backup, target)
        if temp.exists():
            temp.unlink()
        fail(f"Перевірка не пройдена; auction_house_system.py відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ Purchase flow використовує AUCTION_UNCLAIMED_RETENTION_DAYS_V2.")
    print("✅ Невизначена стара retention-константа більше не використовується.")
    print("✅ Транзакційна логіка покупки не змінена.")
    print("Резервні копії:")
    print(f"   {backup.relative_to(root)}")
    print("Перевірки:")
    print("   python -m py_compile ./systems/auction_house_system.py")
    for test_name in TESTS:
        print(f"   python ./tools/{test_name}")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
