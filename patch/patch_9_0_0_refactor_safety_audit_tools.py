from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_0_refactor_safety_audit_tools"
MARKER = "# ✅ ROM REFACTOR SAFETY AUDIT TOOLS V1"

TOOLS = {
    "tools/audit_duplicate_defs.py": r'''#!/usr/bin/env python3
"""
ROM Refactor Tool: audit duplicate function definitions.

Purpose:
- Find functions/classes defined multiple times in a file or across project files.
- Especially useful before cleaning db.py override/hotfix/final-override blocks.

Usage:
    python tools/audit_duplicate_defs.py
    python tools/audit_duplicate_defs.py db.py
    python tools/audit_duplicate_defs.py db.py handlers/combat.py systems
"""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT_TARGETS = ["db.py"]
EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", "backup", "patch", "TXT"}


def iter_python_files(targets: list[str]) -> list[Path]:
    files: list[Path] = []

    for target in targets:
        path = Path(target)

        if not path.exists():
            print(f"[WARN] not found: {path}")
            continue

        if path.is_file() and path.suffix == ".py":
            files.append(path)
            continue

        if path.is_dir():
            for py_file in path.rglob("*.py"):
                if any(part in EXCLUDED_DIRS for part in py_file.parts):
                    continue
                files.append(py_file)

    return sorted(set(files))


def collect_defs(py_file: Path) -> list[tuple[str, int, str]]:
    try:
        text = py_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = py_file.read_text(encoding="utf-8-sig")

    tree = ast.parse(text, filename=str(py_file))
    result: list[tuple[str, int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.append((node.name, node.lineno, "def"))
        elif isinstance(node, ast.ClassDef):
            result.append((node.name, node.lineno, "class"))

    return sorted(result, key=lambda item: item[1])


def main() -> int:
    targets = sys.argv[1:] or DEFAULT_TARGETS
    files = iter_python_files(targets)

    if not files:
        print("No python files found.")
        return 1

    by_name: dict[str, list[tuple[Path, int, str]]] = defaultdict(list)
    duplicates_inside_file: dict[Path, dict[str, list[tuple[int, str]]]] = {}

    for py_file in files:
        file_defs = collect_defs(py_file)
        local: dict[str, list[tuple[int, str]]] = defaultdict(list)

        for name, lineno, kind in file_defs:
            by_name[name].append((py_file, lineno, kind))
            local[name].append((lineno, kind))

        dup_local = {name: rows for name, rows in local.items() if len(rows) > 1}
        if dup_local:
            duplicates_inside_file[py_file] = dup_local

    print("=" * 80)
    print("ROM duplicate definitions audit")
    print("=" * 80)
    print(f"Files scanned: {len(files)}")
    print("")

    if duplicates_inside_file:
        print("[DUPLICATES INSIDE SAME FILE]")
        for py_file, items in duplicates_inside_file.items():
            print(f"\n{py_file}")
            for name, rows in sorted(items.items()):
                places = ", ".join(f"{kind}@{line}" for line, kind in rows)
                print(f"  - {name}: {places}")
    else:
        print("[OK] No duplicate definitions inside scanned files.")

    print("\n" + "=" * 80)
    print("[DUPLICATES ACROSS SCANNED FILES]")
    cross = {name: rows for name, rows in by_name.items() if len(rows) > 1}

    if not cross:
        print("[OK] No duplicate names across scanned files.")
    else:
        for name, rows in sorted(cross.items()):
            print(f"\n{name}")
            for py_file, line, kind in rows:
                print(f"  - {kind} {py_file}:{line}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "tools/check_imports.py": r'''#!/usr/bin/env python3
"""
ROM Refactor Tool: compile/import safety check.

Purpose:
- Compile all Python files outside patch/backup/.venv.
- Optionally import core modules to catch import errors early.

Usage:
    python tools/check_imports.py
"""

from __future__ import annotations

import importlib
import py_compile
import sys
from pathlib import Path

EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", "backup", "patch", "TXT"}
CORE_MODULES = [
    "db",
    "main",
    "keyboards",
    "handlers.start",
    "handlers.profile",
    "handlers.inventory",
    "handlers.combat",
    "systems.combat_system",
    "systems.refine_system",
    "systems.guild_system",
    "systems.auction_house_system",
]


def iter_project_py_files(root: Path) -> list[Path]:
    result: list[Path] = []
    for py_file in root.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in py_file.relative_to(root).parts):
            continue
        result.append(py_file)
    return sorted(result)


def compile_all(root: Path) -> list[str]:
    errors: list[str] = []
    for py_file in iter_project_py_files(root):
        try:
            py_compile.compile(str(py_file), doraise=True)
        except Exception as error:
            errors.append(f"{py_file}: {error}")
    return errors


def import_core_modules() -> list[str]:
    errors: list[str] = []
    for module_name in CORE_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as error:
            errors.append(f"{module_name}: {error}")
    return errors


def main() -> int:
    root = Path.cwd()
    print("=" * 80)
    print("ROM compile/import check")
    print("=" * 80)

    compile_errors = compile_all(root)
    if compile_errors:
        print("\n[COMPILE ERRORS]")
        for error in compile_errors:
            print(f"- {error}")
    else:
        print("[OK] py_compile passed for project files.")

    import_errors = import_core_modules()
    if import_errors:
        print("\n[IMPORT WARNINGS/ERRORS]")
        for error in import_errors:
            print(f"- {error}")
    else:
        print("[OK] core module imports passed.")

    if compile_errors:
        return 1

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "tools/smoke_test_rom_core.py": r'''#!/usr/bin/env python3
"""
ROM Refactor Tool: minimal smoke-test for core public API.

This does NOT modify gameplay state on purpose.
It checks that key functions remain importable/callable after refactor patches.

Usage:
    python tools/smoke_test_rom_core.py
"""

from __future__ import annotations

import traceback

REQUIRED_DB_FUNCTIONS = [
    "init_db",
    "get_user",
    "get_item",
    "get_character_name",
    "get_character_class",
    "get_character_class_display",
    "get_user_mp",
    "set_user_mp",
    "get_max_mp",
    "get_player_stats",
    "get_player_level",
    "get_wallet",
    "get_attack",
    "get_magic_attack",
    "get_max_hp",
    "get_physical_defense",
    "get_magic_defense",
    "get_user_energy",
    "consume_energy_for_hunt",
    "process_passive_regeneration",
    "create_daily_contract",
    "get_active_contract",
    "claim_contract_reward",
    "equip_inventory_item",
    "unequip_inventory_item",
    "repair_equipped_item",
    "repair_all_equipped",
    "get_weapon_damage_by_inventory_id",
    "init_auction_house",
    "init_guild_system",
]


def main() -> int:
    print("=" * 80)
    print("ROM core smoke-test")
    print("=" * 80)

    errors: list[str] = []

    try:
        import db
    except Exception as error:
        print("[FAIL] import db")
        traceback.print_exc()
        return 1

    for name in REQUIRED_DB_FUNCTIONS:
        if not hasattr(db, name):
            errors.append(f"db.{name} missing")

    if errors:
        print("\n[Missing public API]")
        for error in errors:
            print(f"- {error}")
        return 1

    # Lightweight callable checks.
    try:
        db.init_db()
        print("[OK] db.init_db()")
    except Exception as error:
        print(f"[WARN] db.init_db() raised: {error}")

    print("[OK] required public API exists")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "tools/README_refactor_tools.md": r'''# ROM Refactor Tools

Ці інструменти додані перед рефакторингом `db.py`.

## Навіщо

Мета етапу `9.0.0` — нічого не ламати і підготувати safety baseline перед перенесенням логіки з `db.py` у `systems/*`.

## Інструменти

### `audit_duplicate_defs.py`

Шукає duplicate `def` / `class`.

```powershell
python tools/audit_duplicate_defs.py
python tools/audit_duplicate_defs.py db.py
python tools/audit_duplicate_defs.py db.py handlers systems
```

### `check_imports.py`

Компілює `.py` файли і пробує імпортувати core-модулі.

```powershell
python tools/check_imports.py
```

### `smoke_test_rom_core.py`

Перевіряє, що ключовий public API у `db.py` все ще існує.

```powershell
python tools/smoke_test_rom_core.py
```

## Правила рефакторингу

1. Один patch = один домен.
2. `db.py` спочатку лишається compatibility facade.
3. Handlers не переписуємо різко.
4. Після кожного patch:

```powershell
python -m py_compile .\db.py
python tools/check_imports.py
python tools/smoke_test_rom_core.py
```

5. Видаляти старі override-блоки тільки після того, як є нова стабільна реалізація і smoke-tests проходять.
''',
}

REFACTOR_NOTES = r'''# ROM Architecture Refactor 9.0

## Стартовий етап

`9.0.0 — Refactor safety audit tools`

Цей етап нічого не змінює у gameplay-коді.
Він додає інструменти для безпечного аудиту перед підчищенням `db.py`.

## Погоджені правила

1. Один patch = один домен.
2. Перед перенесенням логіки створюємо safety baseline.
3. `db.py` спочатку залишається compatibility facade.
4. Нові системи створюються у `systems/*`.
5. Дані/баланс поступово виносяться у `data/*`.
6. Після кожного етапу виконуються smoke-tests.

## Рекомендований порядок

```text
9.0.0 — audit/safety tools
9.0.1 — systems/character_system.py
9.0.2 — systems/player_system.py
9.0.3 — systems/contract_system.py
9.0.4 — systems/energy_system.py
9.0.5 — systems/regen_system.py
9.0.6 — systems/equipment_system.py read-only helpers
9.0.7 — systems/equipment_system.py equip/unequip/compatibility
9.0.8 — systems/equipment_system.py repair/durability/sell
9.0.9 — data/classes.py and data/equipment_profiles.py
9.0.10 — data/balance.py
9.0.11 — migrations foundation
9.0.12 — final db.py cleanup
```
'''


def make_backup(root: Path, target: Path) -> Path:
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def write_file(root: Path, rel_path: str, content: str):
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)

    backup = None
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if MARKER in existing or existing == content:
            return path, None, False
        backup = make_backup(root, path)

    path.write_text(content, encoding="utf-8")
    return path, backup, True


def main():
    root = Path(__file__).resolve().parents[1]
    changed = []
    backups = []

    for rel_path, body in TOOLS.items():
        content = f"{MARKER}\n" + body
        path, backup, did_change = write_file(root, rel_path, content)
        if did_change:
            changed.append(path)
        if backup:
            backups.append(backup)

    notes_path, backup, did_change = write_file(root, "REFACTOR_9_0_PLAN.md", f"{MARKER}\n" + REFACTOR_NOTES)
    if did_change:
        changed.append(notes_path)
    if backup:
        backups.append(backup)

    # Compile newly created Python tools.
    for rel_path in TOOLS:
        if rel_path.endswith(".py"):
            py_compile.compile(str(root / rel_path), doraise=True)

    print("✅ Патч 9.0.0 Refactor safety audit tools застосовано успішно.")

    if changed:
        print("\nСтворено/оновлено:")
        for path in changed:
            print(f"- {path}")

    if backups:
        print("\nBackup:")
        for path in backups:
            print(f"- {path}")

    print("\nДалі запусти:")
    print("python tools/audit_duplicate_defs.py db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")


if __name__ == "__main__":
    main()
