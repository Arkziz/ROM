#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM patch 9.0.12i2: physical cleanup of Player / Energy / Regen legacy defs.

Run from ROM\\patch:
    ..\\.venv\\Scripts\\python.exe .\\patch_9_0_12i2_player_energy_regen_physical_cleanup.py

The patch:
- keeps the final public db.py wrapper for each migrated API;
- removes only earlier top-level duplicate implementations of the listed APIs;
- does not touch add_exp(), get_user_progress(), equipment, guild, auction,
  notification worker, or class-compatibility captures;
- writes backups only to ROM\\backup.
"""

from __future__ import annotations

import ast
import os
import py_compile
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.12i2"
PATCH_SLUG = "player_energy_regen_physical_cleanup"

PLAYER_FUNCTIONS = (
    "get_player_level",
    "get_wallet",
    "add_gold",
    "add_kill",
    "get_current_hp_raw",
    "get_current_hp",
    "set_current_hp",
    "get_player_stats",
    "get_attack",
    "get_magic_attack",
    "get_max_hp",
    "get_physical_defense",
    "get_magic_defense",
    "get_physical_crit_chance_display",
    "get_magical_crit_chance_display",
    "get_base_dodge_chance_display",
)

ENERGY_FUNCTIONS = (
    "init_energy_system",
    "get_user_energy",
    "consume_energy_for_hunt",
    "restore_energy_for_test",
    "get_users_for_energy_full_notification",
)

REGEN_FUNCTIONS = (
    "init_hp_regen_system",
    "init_passive_regen_system",
    "apply_passive_hp_regen",
    "process_passive_regeneration",
    "reset_hp_regen_timers_now",
)

TARGET_GROUPS = {
    "Player": PLAYER_FUNCTIONS,
    "Energy": ENERGY_FUNCTIONS,
    "Regen": REGEN_FUNCTIONS,
}
TARGET_FUNCTIONS = tuple(
    function_name
    for functions in TARGET_GROUPS.values()
    for function_name in functions
)

PROTECTED_TEXT = (
    "_legacy_equipment_ro_v1_can_equip_item_by_class",
    "_legacy_equipment_ro_v1_can_equip_inventory_item_by_class",
    "_legacy_equipment_ro_v1_is_inventory_item_class_compatible",
)

OUT_OF_SCOPE_FUNCTIONS = (
    "add_exp",
    "get_user_progress",
)


def fail(message: str) -> None:
    print(f"❌ {message}")
    raise SystemExit(1)


def detect_project_root() -> Path:
    script_path = Path(__file__).resolve()
    candidates = (script_path.parent.parent, Path.cwd(), Path.cwd().parent)
    for candidate in candidates:
        candidate = candidate.resolve()
        if (candidate / "db.py").is_file() and (candidate / "systems").is_dir():
            return candidate
    fail("Не знайдено корінь ROM із db.py та папкою systems.")
    raise AssertionError("unreachable")


def read_utf8(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
    try:
        return raw.decode(encoding), encoding
    except UnicodeDecodeError as exc:
        fail(f"Файл {path.name} не вдалося прочитати як UTF-8: {exc}")
    raise AssertionError("unreachable")


def top_level_functions(tree: ast.Module) -> dict[str, list[ast.AST]]:
    result: dict[str, list[ast.AST]] = defaultdict(list)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name].append(node)
    return result


def node_start_line(node: ast.AST) -> int:
    decorators = getattr(node, "decorator_list", None) or []
    if decorators:
        return min([node.lineno] + [decorator.lineno for decorator in decorators])
    return node.lineno


def wrapper_routes_to_system(source: str, node: ast.AST, group: str) -> bool:
    segment = ast.get_source_segment(source, node) or ""
    expected = {
        "Player": "player_system",
        "Energy": "energy_system",
        "Regen": "regen_system",
    }[group]
    return expected in segment


def atomic_write(path: Path, text: str, encoding: str) -> None:
    temp_path = path.with_name(f".{path.name}.{PATCH_ID}.tmp")
    temp_path.write_text(text, encoding=encoding, newline="")
    os.replace(temp_path, path)


def main() -> None:
    root = detect_project_root()
    db_path = root / "db.py"
    backup_dir = root / "backup"

    source, encoding = read_utf8(db_path)
    newline = "\r\n" if "\r\n" in source else "\n"

    try:
        tree = ast.parse(source, filename=str(db_path))
    except SyntaxError as exc:
        fail(f"Початковий db.py має синтаксичну помилку: {exc}")

    functions = top_level_functions(tree)

    missing = [name for name in TARGET_FUNCTIONS if not functions.get(name)]
    if missing:
        fail("У db.py відсутні обов'язкові публічні функції: " + ", ".join(missing))

    protected_before = {name: source.count(name) for name in PROTECTED_TEXT}
    out_of_scope_before = {
        name: len(functions.get(name, [])) for name in OUT_OF_SCOPE_FUNCTIONS
    }

    # The last top-level definition is the active Python definition. For every
    # migrated API it must be a compatibility wrapper into the matching system.
    invalid_wrappers: list[str] = []
    for group, names in TARGET_GROUPS.items():
        for name in names:
            final_node = functions[name][-1]
            if not wrapper_routes_to_system(source, final_node, group):
                invalid_wrappers.append(f"{name} -> {group}")
    if invalid_wrappers:
        fail(
            "Фінальні визначення не схожі на wrappers відповідних systems-модулів: "
            + ", ".join(invalid_wrappers)
        )

    duplicate_counts = {
        name: len(functions[name]) - 1
        for name in TARGET_FUNCTIONS
        if len(functions[name]) > 1
    }

    if not duplicate_counts:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано: дублікати Player / Energy / Regen відсутні.")
        print("✅ db.py не змінено.")
        return

    ranges: list[tuple[int, int, str, str]] = []
    for group, names in TARGET_GROUPS.items():
        for name in names:
            for node in functions[name][:-1]:
                if node.end_lineno is None:
                    fail(f"Не вдалося визначити кінець функції {name}.")
                ranges.append((node_start_line(node), node.end_lineno, group, name))

    # Defensive overlap check before editing line ranges.
    ordered = sorted(ranges)
    for previous, current in zip(ordered, ordered[1:]):
        if current[0] <= previous[1]:
            fail(
                "Виявлено перетин діапазонів видалення: "
                f"{previous[3]} і {current[3]}. db.py не змінено."
            )

    lines = source.splitlines(keepends=True)
    for start, end, _group, _name in sorted(ranges, reverse=True):
        del lines[start - 1:end]
    updated = "".join(lines)

    if newline == "\r\n" and "\r\n" not in updated:
        updated = updated.replace("\n", "\r\n")

    try:
        updated_tree = ast.parse(updated, filename=str(db_path))
    except SyntaxError as exc:
        fail(f"Згенерований db.py не пройшов AST-перевірку: {exc}")

    updated_functions = top_level_functions(updated_tree)
    bad_counts = {
        name: len(updated_functions.get(name, []))
        for name in TARGET_FUNCTIONS
        if len(updated_functions.get(name, [])) != 1
    }
    if bad_counts:
        fail(f"Після очищення порушено кількість wrappers: {bad_counts}")

    protected_after = {name: updated.count(name) for name in PROTECTED_TEXT}
    if protected_after != protected_before:
        fail("Перевірка class-compatibility captures не пройдена; db.py не змінено.")

    out_of_scope_after = {
        name: len(updated_functions.get(name, [])) for name in OUT_OF_SCOPE_FUNCTIONS
    }
    if out_of_scope_after != out_of_scope_before:
        fail("Патч зачепив add_exp/get_user_progress; db.py не змінено.")

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"db.py_{PATCH_ID}_{PATCH_SLUG}_{timestamp}.bak"
    shutil.copy2(db_path, backup_path)

    try:
        atomic_write(db_path, updated, encoding)
        py_compile.compile(str(db_path), doraise=True)
    except Exception as exc:
        shutil.copy2(backup_path, db_path)
        fail(f"Перевірка після запису не пройдена; db.py відновлено з backup: {exc}")

    removed_by_group = defaultdict(int)
    for _start, _end, group, _name in ranges:
        removed_by_group[group] += 1

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ Фізично видалено старі дублікати реалізацій із db.py:")
    for group in ("Player", "Energy", "Regen"):
        print(f"   • {group}: {removed_by_group[group]}")
    print(f"✅ Загалом видалено визначень: {len(ranges)}")
    print(f"✅ Залишено по одному публічному wrapper для {len(TARGET_FUNCTIONS)} API-функцій.")
    print("✅ add_exp/get_user_progress не змінено.")
    print("✅ Class-compatibility equipment captures не змінено.")
    print("✅ Синтаксична перевірка db.py пройдена.")
    print("Резервні копії:")
    print(f"   {backup_path.relative_to(root)}")
    print("Перевірки:")
    print("   python -m py_compile .\\db.py")
    print("   python tools/check_imports.py")
    print("   python tools/smoke_test_rom_core.py")
    print("   python tools/smoke_test_player_contracts.py")
    print("   python tools/smoke_test_player_combat_stats.py")
    print("   python tools/smoke_test_energy_contracts.py")
    print("   python tools/smoke_test_regen_contracts.py")
    print("   python tools/smoke_test_equipment_readonly_core.py")
    print("   python tools/smoke_test_inventory_refine_contracts.py")
    print("   python tools/smoke_test_weapon_damage_contracts.py")
    print("   python tools/smoke_test_equipment_write_contracts.py")
    print("   python tools/smoke_test_equipment_durability_contracts.py")
    print("   python tools/smoke_test_equipment_trader_contracts.py")
    print("   python tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
