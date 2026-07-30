#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13n: canonicalize duplicated db.py constants through data modules."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.13n"
TARGET_REL = Path("db.py")
TEST_NAME = "smoke_test_constants_canonicalization.py"

CANONICAL_GROUPS = {
    "data.classes": (
        "CLASS_CONFIGS",
        "CLASS_RESET_SPHERE_ITEM_ID",
    ),
    "data.equipment_profiles": (
        "ARMOR_ALLOWED_BY_CLASS",
        "ARMOR_EXTRA_STATS_BY_SLOT",
        "ARMOR_TYPE_LABELS",
        "EQUIPMENT_SLOTS",
        "ITEM_SUBTYPE_LABELS",
        "MAIN_HAND_ALLOWED_BY_CLASS",
        "MAIN_HAND_PROFILES",
        "OFF_HAND_ALLOWED_BY_CLASS",
        "OFF_HAND_PROFILES",
    ),
    "data.balance": (
        "CONTRACTS_UNLOCK_LEVEL",
        "CONTRACT_MOBS_EQUIVALENT",
        "CONTRACT_TARGET_KILLS",
        "DAILY_CONTRACT_LIMIT",
        "DAILY_QUEST_ID_KILL_MONSTERS",
        "DAILY_QUEST_REWARD_ITEM_ID",
        "DAILY_QUEST_REWARD_QUANTITY",
        "DAILY_QUEST_TARGET_KILLS",
        "ENERGY_MAX",
        "ENERGY_REGEN_MINUTES",
        "HP_REGEN_MINUTES",
        "HP_REGEN_PERCENT",
        "RARITY_REPAIR_MULTIPLIERS",
        "REFINE_MATERIAL_MAX_STACK",
        "REFINE_STONE_ITEM_ID",
    ),
}
ALL_CONSTANTS = tuple(
    name for names in CANONICAL_GROUPS.values() for name in names
)

TEST_SOURCE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only contracts for db.py constants canonicalization."""
from __future__ import annotations

import ast
import hashlib
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "game.db"
DB_PY = ROOT / "db.py"
CANONICAL_GROUPS = {
    "data.classes": (
        "CLASS_CONFIGS", "CLASS_RESET_SPHERE_ITEM_ID",
    ),
    "data.equipment_profiles": (
        "ARMOR_ALLOWED_BY_CLASS", "ARMOR_EXTRA_STATS_BY_SLOT",
        "ARMOR_TYPE_LABELS", "EQUIPMENT_SLOTS", "ITEM_SUBTYPE_LABELS",
        "MAIN_HAND_ALLOWED_BY_CLASS", "MAIN_HAND_PROFILES",
        "OFF_HAND_ALLOWED_BY_CLASS", "OFF_HAND_PROFILES",
    ),
    "data.balance": (
        "CONTRACTS_UNLOCK_LEVEL", "CONTRACT_MOBS_EQUIVALENT",
        "CONTRACT_TARGET_KILLS", "DAILY_CONTRACT_LIMIT",
        "DAILY_QUEST_ID_KILL_MONSTERS", "DAILY_QUEST_REWARD_ITEM_ID",
        "DAILY_QUEST_REWARD_QUANTITY", "DAILY_QUEST_TARGET_KILLS",
        "ENERGY_MAX", "ENERGY_REGEN_MINUTES", "HP_REGEN_MINUTES",
        "HP_REGEN_PERCENT", "RARITY_REPAIR_MULTIPLIERS",
        "REFINE_MATERIAL_MAX_STACK", "REFINE_STONE_ITEM_ID",
    ),
}
ALL_CONSTANTS = tuple(name for values in CANONICAL_GROUPS.values() for name in values)


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint():
    return (
        hashlib.sha256(DB_PATH.read_bytes()).hexdigest(),
        DB_PATH.stat().st_size,
        DB_PATH.stat().st_mtime_ns,
    )


def assigned_names(node):
    names = set()
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    for target in targets:
        if isinstance(target, ast.Name):
            names.add(target.id)
    return names


def main():
    before = fingerprint()
    source = DB_PY.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(DB_PY))

    local_definitions = []
    imported = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            overlap = assigned_names(node).intersection(ALL_CONSTANTS)
            if overlap:
                local_definitions.extend((name, node.lineno) for name in overlap)
        elif isinstance(node, ast.ImportFrom) and node.module in CANONICAL_GROUPS:
            for alias in node.names:
                imported[alias.asname or alias.name] = node.module

    if local_definitions:
        fail(f"local duplicate definitions remain: {local_definitions}")

    missing_imports = [
        name for module, names in CANONICAL_GROUPS.items() for name in names
        if imported.get(name) != module
    ]
    if missing_imports:
        fail(f"canonical imports missing or owned by wrong module: {missing_imports}")

    import db
    identity_checks = 0
    value_checks = 0
    for module_name, names in CANONICAL_GROUPS.items():
        canonical = importlib.import_module(module_name)
        for name in names:
            if not hasattr(db, name):
                fail(f"db public constant missing: {name}")
            if not hasattr(canonical, name):
                fail(f"canonical constant missing: {module_name}.{name}")
            db_value = getattr(db, name)
            canonical_value = getattr(canonical, name)
            if db_value != canonical_value:
                fail(f"value mismatch: db.{name} != {module_name}.{name}")
            value_checks += 1
            if isinstance(canonical_value, (dict, list, set)):
                if db_value is not canonical_value:
                    fail(f"identity mismatch for mutable canonical object: {name}")
                identity_checks += 1

    required_runtime = {
        "class_name": db.get_class_display_name_by_key("mage"),
        "armor_label": db.get_armor_type_label("cloth"),
        "subtype_label": db.get_item_subtype_label("sword_1h"),
        "repair_multiplier": db.get_rarity_repair_multiplier("epic"),
        "contract_exp": db.get_contract_exp_for_level(10),
    }
    if not required_runtime["class_name"] or not required_runtime["armor_label"]:
        fail(f"runtime helper output invalid: {required_runtime}")

    if before != fingerprint():
        fail("game.db changed during read-only contracts")

    print("[OK] constants canonicalization contracts")
    print(f"- local duplicate definitions: {len(local_definitions)}")
    print(f"- canonical imports verified: {value_checks}")
    print(f"- mutable object identity checks: {identity_checks}")
    print(f"- public db constant surface preserved: {len(ALL_CONSTANTS)}")
    print(f"- runtime helper probes: {required_runtime}")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
'''


def fail(message):
    print(f"❌ {message}")
    raise SystemExit(1)


def find_root():
    here = Path(__file__).resolve()
    for root in (here.parent.parent, Path.cwd(), Path.cwd().parent):
        root = root.resolve()
        if (
            (root / TARGET_REL).is_file()
            and (root / "game.db").is_file()
            and (root / "data" / "classes.py").is_file()
            and (root / "data" / "equipment_profiles.py").is_file()
            and (root / "data" / "balance.py").is_file()
        ):
            return root
    fail("Не знайдено корінь ROM або canonical data modules.")


def assigned_names(node):
    result = set()
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    for target in targets:
        if isinstance(target, ast.Name):
            result.add(target.id)
    return result


def literal_definitions(source):
    tree = ast.parse(source)
    result = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        overlap = assigned_names(node).intersection(ALL_CONSTANTS)
        if overlap:
            result.append((node, overlap))
    return result


def canonical_values(root):
    values = {}
    for module_name, names in CANONICAL_GROUPS.items():
        path = root / Path(*module_name.split(".")).with_suffix(".py")
        text = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(text, filename=str(path))
        definitions = {}
        for node in tree.body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            for name in assigned_names(node):
                if name not in names:
                    continue
                value_node = node.value
                try:
                    definitions[name] = ast.literal_eval(value_node)
                except Exception as exc:
                    raise RuntimeError(f"canonical constant is not literal: {module_name}.{name}: {exc}")
        missing = sorted(set(names) - set(definitions))
        if missing:
            raise RuntimeError(f"canonical constants missing in {module_name}: {missing}")
        for name in names:
            values[name] = (module_name, definitions[name])
    return values


def validate_local_values(source, canonical):
    definitions = literal_definitions(source)
    found = {name: [] for name in ALL_CONSTANTS}
    for node, names in definitions:
        try:
            value = ast.literal_eval(node.value)
        except Exception as exc:
            raise RuntimeError(f"local constant at line {node.lineno} is not literal: {exc}")
        for name in names:
            found[name].append((node.lineno, value))

    missing = sorted(name for name, rows in found.items() if not rows)
    if missing:
        raise RuntimeError(f"expected local definitions not found: {missing}")

    # Python resolves module globals when a function is called, not when the
    # function is defined. Therefore an earlier historical definition may
    # differ, while the final effective definition is the real runtime contract.
    # This is expected for MAIN_HAND_PROFILES and is precisely why all local
    # definitions must be replaced by one early canonical import.
    historical_differences = {}
    for name, rows in found.items():
        expected = canonical[name][1]
        final_line, final_value = rows[-1]
        if final_value != expected:
            raise RuntimeError(
                f"final local/canonical mismatch for {name} at line {final_line}"
            )
        differing = [line for line, value in rows[:-1] if value != expected]
        if differing:
            historical_differences[name] = differing

    return definitions, found, historical_differences


def remove_definitions(source, definitions):
    lines = source.splitlines(keepends=True)
    for node, _names in sorted(definitions, key=lambda item: item[0].lineno, reverse=True):
        start = node.lineno - 1
        end = node.end_lineno
        if end < len(lines) and not lines[end].strip():
            end += 1
        lines[start:end] = []
    updated = "".join(lines)
    ast.parse(updated, filename="db.py")
    return updated


def add_canonical_imports(source):
    tree = ast.parse(source)
    existing = {
        (node.module, alias.asname or alias.name)
        for node in tree.body if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    blocks = []
    for module_name, names in CANONICAL_GROUPS.items():
        missing = [name for name in names if (module_name, name) not in existing]
        if missing:
            body = "\n".join(f"    {name}," for name in missing)
            blocks.append(f"from {module_name} import (\n{body}\n)\n")
    if not blocks:
        return source

    # Insert after the initial import section but before the first constant or
    # consumer. This keeps public names available throughout the module.
    insert_line = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            insert_line = max(insert_line, node.end_lineno)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            insert_line = max(insert_line, node.end_lineno)
        else:
            break
    lines = source.splitlines(keepends=True)
    lines[insert_line:insert_line] = ["\n" + "\n".join(blocks) + "\n"]
    updated = "".join(lines)
    ast.parse(updated, filename="db.py")
    return updated


def validate_updated(source):
    tree = ast.parse(source, filename="db.py")
    residual = []
    imported = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            overlap = assigned_names(node).intersection(ALL_CONSTANTS)
            residual.extend((name, node.lineno) for name in overlap)
        elif isinstance(node, ast.ImportFrom) and node.module in CANONICAL_GROUPS:
            for alias in node.names:
                imported[alias.asname or alias.name] = node.module
    if residual:
        raise RuntimeError(f"local constant definitions remain: {residual}")
    missing = [
        name for module, names in CANONICAL_GROUPS.items() for name in names
        if imported.get(name) != module
    ]
    if missing:
        raise RuntimeError(f"canonical imports missing: {missing}")


def run_checked(root, path, label, env):
    result = subprocess.run([sys.executable, str(path)], cwd=root, env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{label} exit code {result.returncode}")


def main():
    root = find_root()
    target = root / TARGET_REL
    tools = root / "tools"
    test_path = tools / TEST_NAME

    tests = [
        TEST_NAME,
        "smoke_test_character_mutation_contracts.py",
        "smoke_test_contract_contracts.py",
        "smoke_test_inventory_refine_contracts.py",
        "smoke_test_equipment_readonly_core.py",
        "smoke_test_equipment_trader_contracts.py",
        "smoke_test_player_combat_stats.py",
        "smoke_test_rom_core.py",
        "check_imports.py",
    ]
    for name in tests[1:]:
        if not (tools / name).is_file():
            fail(f"Відсутній tools/{name}.")

    source = target.read_text(encoding="utf-8-sig")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    if not literal_definitions(source):
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
        test_path.write_text(TEST_SOURCE, encoding="utf-8")
        for name in tests:
            run_checked(root, tools / name, name, env)
        return

    canonical = canonical_values(root)
    definitions, found, historical_differences = validate_local_values(source, canonical)
    updated = remove_definitions(source, definitions)
    updated = add_canonical_imports(updated)
    validate_updated(updated)

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    code_backup = backup_dir / f"db.py_{PATCH_ID}_{stamp}.bak"
    test_backup = None
    shutil.copy2(target, code_backup)
    if test_path.exists():
        test_backup = backup_dir / f"tools_{TEST_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(test_path, test_backup)

    try:
        target.write_text(updated, encoding="utf-8")
        test_path.write_text(TEST_SOURCE, encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
        py_compile.compile(str(test_path), doraise=True)

        for name in tests:
            run_checked(root, tools / name, name, env)

        readiness = subprocess.run(
            [sys.executable, str(tools / "db_cleanup_readiness.py")],
            cwd=root, env=env, text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=False,
        )
        print(readiness.stdout, end="")
        if readiness.returncode != 0:
            raise RuntimeError(f"readiness exit code {readiness.returncode}")
        for marker in (
            "duplicates: 0", "legacy_refs: 0",
            "unsafe_delete: 0", "maybe_cleanup_later: 0",
        ):
            if marker not in readiness.stdout:
                raise RuntimeError(f"readiness missing {marker}")

    except Exception as exc:
        shutil.copy2(code_backup, target)
        if test_backup is not None:
            shutil.copy2(test_backup, test_path)
        elif test_path.exists():
            test_path.unlink()
        fail(f"Перевірка не пройдена; db.py і тест відновлено: {exc}")

    removed_definitions = sum(len(rows) for rows in found.values())
    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print(f"✅ Канонізовано констант: {len(ALL_CONSTANTS)}")
    print(f"✅ Видалено локальних визначень у db.py: {removed_definitions}")
    print(f"✅ Історичні проміжні розбіжності замінено canonical import: {historical_differences}")
    print("✅ Джерела істини: data.classes / data.equipment_profiles / data.balance.")
    print("✅ Public db.<CONSTANT> API збережено через прямі canonical imports.")
    print("✅ Gameplay-код і game.db не змінено.")
    print("Резервні копії:")
    print(f"   {code_backup.relative_to(root)}")
    if test_backup is not None:
        print(f"   {test_backup.relative_to(root)}")
    print("Перевірки:")
    for name in tests:
        print(f"   python ./tools/{name}")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
