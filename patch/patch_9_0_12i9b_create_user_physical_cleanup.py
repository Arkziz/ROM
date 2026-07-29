#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i9b: remove earlier create_user definitions from db.py."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.12i9b"
TARGET = "create_user"
PRESERVE = "claim_contract_reward"
CREATE_USER_TEST = "smoke_test_create_user_contracts.py"
TESTS = (
    CREATE_USER_TEST,
    "smoke_test_energy_contracts.py",
    "smoke_test_character_mutation_contracts.py",
    "smoke_test_equipment_readonly_core.py",
    "smoke_test_rom_core.py",
    "check_imports.py",
)
REQUIRED_FINAL_MARKERS = (
    "init_energy_system",
    "ensure_equipment_slots",
    "migrate_legacy_equipment_to_slots",
    "expand_bag_slots_to_40",
    "energy_full_notified",
    "last_energy_update",
    "ENERGY_MAX",
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
            and (root / "tools" / CREATE_USER_TEST).is_file()
            and (root / "tools" / "db_cleanup_readiness.py").is_file()
        ):
            return root
    fail("Не знайдено корінь ROM.")


def function_map(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.setdefault(node.name, []).append(node)
    return result


def node_start(node):
    decorators = getattr(node, "decorator_list", None) or []
    return min([node.lineno] + [decorator.lineno for decorator in decorators])


def run_checked(root, path, label):
    result = subprocess.run([sys.executable, str(path)], cwd=root, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{label} exit code {result.returncode}")


def update_test_contract(test_source):
    old = 'if len(definitions)!=3: fail(f"create_user definitions={len(definitions)}, expected 3")'
    new = 'if len(definitions)!=1: fail(f"create_user definitions={len(definitions)}, expected 1 after i9b")'
    if old in test_source:
        return test_source.replace(old, new, 1)
    if new in test_source:
        return test_source
    raise RuntimeError("Не знайдено структурний контракт create_user у тесті i9a/i9b")


def main():
    root = find_root()
    db_path = root / "db.py"
    tools = root / "tools"
    test_path = tools / CREATE_USER_TEST
    readiness_path = tools / "db_cleanup_readiness.py"

    for test_name in TESTS:
        if not (tools / test_name).is_file():
            fail(f"Відсутній tools/{test_name}.")

    source = db_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(db_path))
    definitions = function_map(tree)

    already_clean = len(definitions.get(TARGET, [])) == 1
    if already_clean:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
        test_source = test_path.read_text(encoding="utf-8-sig")
        updated_test = update_test_contract(test_source)
        if updated_test != test_source:
            test_path.write_text(updated_test, encoding="utf-8")
        for test_name in TESTS:
            run_checked(root, tools / test_name, test_name)
        return

    target_nodes = definitions.get(TARGET, [])
    if len(target_nodes) != 3:
        fail(f"db.py create_user: definitions={len(target_nodes)}, очікувалося 3.")

    preserve_before = len(definitions.get(PRESERVE, []))
    if preserve_before != 2:
        fail(f"db.py claim_contract_reward: definitions={preserve_before}, очікувалося 2.")

    final_node = target_nodes[-1]
    final_source = ast.get_source_segment(source, final_node) or ""
    for marker in REQUIRED_FINAL_MARKERS:
        if marker not in final_source:
            fail(f"Фінальна create_user не містить обов'язковий marker: {marker}")

    remove_ranges = [
        (node_start(node), node.end_lineno, TARGET)
        for node in target_nodes[:-1]
    ]
    ordered = sorted(remove_ranges)
    for previous, current in zip(ordered, ordered[1:]):
        if current[0] <= previous[1]:
            fail("Діапазони ранніх create_user перетинаються.")

    lines = source.splitlines(keepends=True)
    for start, end, _name in sorted(remove_ranges, reverse=True):
        del lines[start - 1:end]
    updated = "".join(lines)

    updated_tree = ast.parse(updated, filename=str(db_path))
    updated_definitions = function_map(updated_tree)
    if len(updated_definitions.get(TARGET, [])) != 1:
        fail(f"Після очищення create_user definitions={len(updated_definitions.get(TARGET, []))}")
    if len(updated_definitions.get(PRESERVE, [])) != preserve_before:
        fail("Патч зачепив claim_contract_reward.")

    retained_source = ast.get_source_segment(updated, updated_definitions[TARGET][0]) or ""
    for marker in REQUIRED_FINAL_MARKERS:
        if marker not in retained_source:
            fail(f"Після очищення create_user втратила marker: {marker}")

    duplicates_after = {
        name for name, nodes in updated_definitions.items() if len(nodes) > 1
    }
    if duplicates_after != {PRESERVE}:
        fail(f"Після очищення неочікувані duplicates: {sorted(duplicates_after)}")

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_backup = backup_dir / f"db.py_{PATCH_ID}_create_user_cleanup_{stamp}.bak"
    test_backup = backup_dir / f"tools_{CREATE_USER_TEST}_{PATCH_ID}_{stamp}.bak"
    shutil.copy2(db_path, db_backup)
    shutil.copy2(test_path, test_backup)

    temp = db_path.with_name(".db.i9b.tmp")
    try:
        temp.write_text(updated, encoding="utf-8")
        os.replace(temp, db_path)

        test_source = test_path.read_text(encoding="utf-8-sig")
        test_path.write_text(update_test_contract(test_source), encoding="utf-8")

        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(test_path), doraise=True)

        for test_name in TESTS:
            run_checked(root, tools / test_name, test_name)

        readiness = subprocess.run(
            [sys.executable, str(readiness_path)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        print(readiness.stdout, end="")
        if readiness.returncode != 0:
            raise RuntimeError(f"readiness exit code {readiness.returncode}")

        for expected in (
            "definitions: 351",
            "duplicates: 1",
            "legacy_refs: 0",
            "unsafe_delete: 0",
            "maybe_cleanup_later: 1",
        ):
            if expected not in readiness.stdout:
                raise RuntimeError(f"readiness не містить очікуване значення: {expected}")

    except Exception as exc:
        shutil.copy2(db_backup, db_path)
        shutil.copy2(test_backup, test_path)
        if temp.exists():
            temp.unlink()
        fail(f"Перевірка не пройдена; db.py і create_user test відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ Фізично видалено ранніх create_user визначень: 2")
    print("✅ Залишено фінальну create_user з Energy та 10 equipment slots.")
    print("✅ claim_contract_reward не змінено.")
    print("✅ Залишилося duplicate groups: 1.")
    print("Резервні копії:")
    print(f"   {db_backup.relative_to(root)}")
    print(f"   {test_backup.relative_to(root)}")
    print("Перевірки:")
    print("   python -m py_compile ./db.py")
    for test_name in TESTS:
        print(f"   python ./tools/{test_name}")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
