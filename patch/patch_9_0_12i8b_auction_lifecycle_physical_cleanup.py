#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i8b: remove earlier Auction lifecycle definitions from db.py."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.12i8b"
TARGETS = ("init_auction_house", "update_expired_auction_lots")
PRESERVE = ("create_user", "claim_contract_reward")
AUCTION_TEST = "smoke_test_auction_lifecycle_contracts.py"
TESTS = (
    AUCTION_TEST,
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


def main():
    root = find_root()
    db_path = root / "db.py"
    system_path = root / "systems" / "auction_house_system.py"
    tools = root / "tools"
    readiness_path = tools / "db_cleanup_readiness.py"

    for test_name in TESTS:
        if not (tools / test_name).is_file():
            fail(f"Відсутній tools/{test_name}.")

    source = db_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(db_path))
    definitions = function_map(tree)

    already_clean = all(len(definitions.get(name, [])) == 1 for name in TARGETS)
    if already_clean:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
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
            fail(f"Readiness exit code {readiness.returncode}")
        return

    preserve_before = {name: len(definitions.get(name, [])) for name in PRESERVE}
    if preserve_before != {"create_user": 3, "claim_contract_reward": 2}:
        fail(f"Неочікуваний стан збережених груп: {preserve_before}")

    system_source = system_path.read_text(encoding="utf-8-sig")
    system_tree = ast.parse(system_source, filename=str(system_path))
    system_definitions = function_map(system_tree)

    remove_ranges = []
    removed_by_name = {}
    for name in TARGETS:
        nodes = definitions.get(name, [])
        if len(nodes) != 2:
            fail(f"db.py {name}: definitions={len(nodes)}, очікувалося 2.")

        final_source = ast.get_source_segment(source, nodes[-1]) or ""
        if "auction_house_system" not in final_source:
            fail(f"Фінальна db.{name} не делегує в auction_house_system.")

        if not system_definitions.get(name):
            fail(f"systems/auction_house_system.py не містить {name}.")

        removed_by_name[name] = 1
        old_node = nodes[0]
        remove_ranges.append((node_start(old_node), old_node.end_lineno, name))

    ordered = sorted(remove_ranges)
    for previous, current in zip(ordered, ordered[1:]):
        if current[0] <= previous[1]:
            fail(f"Діапазони видалення перетинаються: {previous[2]} / {current[2]}")

    lines = source.splitlines(keepends=True)
    for start, end, _name in sorted(remove_ranges, reverse=True):
        del lines[start - 1:end]
    updated = "".join(lines)

    updated_tree = ast.parse(updated, filename=str(db_path))
    updated_definitions = function_map(updated_tree)

    for name in TARGETS:
        nodes = updated_definitions.get(name, [])
        if len(nodes) != 1:
            fail(f"Після очищення db.{name}: definitions={len(nodes)}")
        final_source = ast.get_source_segment(updated, nodes[0]) or ""
        if "auction_house_system" not in final_source:
            fail(f"Після очищення db.{name} не є Auction System wrapper.")

    preserve_after = {name: len(updated_definitions.get(name, [])) for name in PRESERVE}
    if preserve_after != preserve_before:
        fail("Патч зачепив create_user або claim_contract_reward.")

    duplicates_after = {
        name for name, nodes in updated_definitions.items() if len(nodes) > 1
    }
    if duplicates_after != set(PRESERVE):
        fail(f"Після очищення неочікувані duplicates: {sorted(duplicates_after)}")

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"db.py_{PATCH_ID}_auction_lifecycle_cleanup_{stamp}.bak"
    shutil.copy2(db_path, backup)
    auction_test_path = tools / AUCTION_TEST
    auction_test_backup = backup_dir / f"tools_{AUCTION_TEST}_{PATCH_ID}_{stamp}.bak"
    shutil.copy2(auction_test_path, auction_test_backup)

    temp = db_path.with_name(".db.i8b.tmp")
    try:
        temp.write_text(updated, encoding="utf-8")
        os.replace(temp, db_path)

        test_source = auction_test_path.read_text(encoding="utf-8-sig")
        old_contract = 'if len(db_defs.get(name,[]))!=2: fail(f"db.py {name}: definitions={len(db_defs.get(name,[]))}, expected 2")'
        new_contract = 'if len(db_defs.get(name,[]))!=1: fail(f"db.py {name}: definitions={len(db_defs.get(name,[]))}, expected 1 after i8b")'
        if old_contract in test_source:
            test_source = test_source.replace(old_contract, new_contract, 1)
            auction_test_path.write_text(test_source, encoding="utf-8")
        elif new_contract not in test_source:
            raise RuntimeError("Не знайдено структурний контракт i8a/i8b у Auction lifecycle test")

        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(system_path), doraise=True)
        py_compile.compile(str(auction_test_path), doraise=True)

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

        expected_metrics = (
            "definitions: 353",
            "duplicates: 2",
            "legacy_refs: 0",
            "unsafe_delete: 0",
            "maybe_cleanup_later: 2",
        )
        for expected in expected_metrics:
            if expected not in readiness.stdout:
                raise RuntimeError(f"readiness не містить очікуване значення: {expected}")

    except Exception as exc:
        shutil.copy2(backup, db_path)
        shutil.copy2(auction_test_backup, auction_test_path)
        if temp.exists():
            temp.unlink()
        fail(f"Перевірка не пройдена; db.py і Auction lifecycle test відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print(f"✅ Фізично видалено ранніх Auction lifecycle визначень: {sum(removed_by_name.values())}")
    print("✅ Залишено фінальні wrappers для init_auction_house та update_expired_auction_lots.")
    print("✅ create_user і claim_contract_reward не змінені.")
    print("✅ Залишилося duplicate groups: 2.")
    print("Резервні копії:")
    print(f"   {backup.relative_to(root)}")
    print(f"   {auction_test_backup.relative_to(root)}")
    print("Перевірки:")
    print("   python -m py_compile ./db.py")
    print("   python -m py_compile ./systems/auction_house_system.py")
    for test_name in TESTS:
        print(f"   python ./tools/{test_name}")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
