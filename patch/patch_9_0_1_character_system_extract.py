from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_1_character_system_extract"
DB_TARGET = Path("db.py")
CHARACTER_TARGET = Path("systems") / "character_system.py"
DB_MARKER = "# ✅ ROM 9.0.1 CHARACTER SYSTEM FACADE WRAPPERS V1"
CHARACTER_MARKER = "# ✅ ROM 9.0.1 CHARACTER SYSTEM V1"

CHARACTER_CODE = r'''# ✅ ROM 9.0.1 CHARACTER SYSTEM V1
"""
ROM Character System v1.

Goal of 9.0.1:
- create a dedicated character domain module;
- move public character/class/MP API behind systems.character_system;
- keep behavior stable by using legacy db.py implementations if they exist;
- keep db.py as compatibility facade for existing handlers.

This is intentionally conservative. It does not delete old db.py code yet.
Final cleanup will happen after all refactor stages and smoke-tests.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional


DEFAULT_CLASS_CONFIGS = {
    "warrior": {
        "name": "🛡️ Воїн",
        "resource": "rage",
        "description": "Фізичний боєць ближнього бою.",
        "main_stats": ["str", "sta"],
    },
    "knight": {
        "name": "⚔️ Лицар",
        "resource": "rage",
        "description": "Захисний боєць у важкій броні.",
        "main_stats": ["sta", "str"],
    },
    "scout": {
        "name": "🏹 Скаут",
        "resource": "combat_energy",
        "description": "Фізичний боєць із луком та пастками.",
        "main_stats": ["dex", "str"],
    },
    "rogue": {
        "name": "🗡️ Розбійник",
        "resource": "combat_energy_combo",
        "description": "Швидкий фізичний боєць із комбо.",
        "main_stats": ["dex", "str"],
    },
    "mage": {
        "name": "🔮 Маг",
        "resource": "mana",
        "description": "Магічний damage dealer.",
        "main_stats": ["int", "wis"],
    },
    "priest": {
        "name": "⚕️ Жрець",
        "resource": "mana",
        "description": "Магічний support із лікуванням та очищенням.",
        "main_stats": ["wis", "int"],
    },
}


CLASS_RESET_SPHERE_ITEM_ID = 301


def _db_module():
    import db
    return db


def _legacy_function(name: str) -> Optional[Callable[..., Any]]:
    db = _db_module()
    return getattr(db, f"_legacy_{name}_before_character_system_v1", None)


def _legacy_value(name: str, default: Any = None) -> Any:
    db = _db_module()
    return getattr(db, f"_legacy_{name}_before_character_system_v1", default)


def get_class_configs() -> dict:
    return _legacy_value("CLASS_CONFIGS", DEFAULT_CLASS_CONFIGS)


# Keep CLASS_CONFIGS as module-level public data for imports that expect it.
CLASS_CONFIGS = get_class_configs()


def _fetchone(sql: str, params: tuple = ()):  # sqlite3.Row or tuple depending on project state
    db = _db_module()
    db.cursor.execute(sql, params)
    return db.cursor.fetchone()


def _execute_commit(sql: str, params: tuple = ()):
    db = _db_module()
    db.cursor.execute(sql, params)
    db.conn.commit()


def _row_get(row, key: str, index: int = 0, default=None):
    if row is None:
        return default
    try:
        return row[key]
    except Exception:
        pass
    try:
        return row[index]
    except Exception:
        return default


def normalize_character_name(name: str) -> str:
    legacy = _legacy_function("normalize_character_name")
    if legacy:
        return legacy(name)

    return " ".join(str(name or "").strip().split())


def validate_character_name(name: str):
    legacy = _legacy_function("validate_character_name")
    if legacy:
        return legacy(name)

    normalized = normalize_character_name(name)

    if not normalized:
        return False, "❌ Ім'я не може бути порожнім."

    if len(normalized) < 2:
        return False, "❌ Ім'я має містити мінімум 2 символи."

    if len(normalized) > 20:
        return False, "❌ Ім'я має містити максимум 20 символів."

    if not re.match(r"^[\wА-Яа-яІіЇїЄєҐґ'’\- ]+$", normalized, flags=re.UNICODE):
        return False, "❌ Ім'я містить недозволені символи."

    return True, normalized


def get_character_name(user_id: int):
    legacy = _legacy_function("get_character_name")
    if legacy:
        return legacy(user_id)

    row = _fetchone("SELECT character_name FROM users WHERE user_id=?", (user_id,))
    return _row_get(row, "character_name", 0, None)


def set_character_name(user_id: int, name: str):
    legacy = _legacy_function("set_character_name")
    if legacy:
        return legacy(user_id, name)

    normalized = normalize_character_name(name)
    _execute_commit(
        "UPDATE users SET character_name=? WHERE user_id=?",
        (normalized, user_id),
    )
    return True


def get_character_class(user_id: int):
    legacy = _legacy_function("get_character_class")
    if legacy:
        return legacy(user_id)

    row = _fetchone("SELECT class_key FROM users WHERE user_id=?", (user_id,))
    return _row_get(row, "class_key", 0, None)


def set_character_class(user_id: int, class_key: str):
    legacy = _legacy_function("set_character_class")
    if legacy:
        return legacy(user_id, class_key)

    if class_key not in get_class_configs():
        return False

    _execute_commit(
        "UPDATE users SET class_key=? WHERE user_id=?",
        (class_key, user_id),
    )
    return True


def get_character_class_display(user_id: int):
    legacy = _legacy_function("get_character_class_display")
    if legacy:
        return legacy(user_id)

    class_key = get_character_class(user_id)
    config = get_class_configs().get(class_key or "")
    if not config:
        return "Без класу"
    return config.get("name", class_key)


def get_character_resource_type(user_id: int):
    legacy = _legacy_function("get_character_resource_type")
    if legacy:
        return legacy(user_id)

    class_key = get_character_class(user_id)
    return get_class_configs().get(class_key or "", {}).get("resource", "mana")


def get_user_mp(user_id: int):
    legacy = _legacy_function("get_user_mp")
    if legacy:
        return legacy(user_id)

    row = _fetchone("SELECT mp, max_mp FROM users WHERE user_id=?", (user_id,))
    return {
        "mp": int(_row_get(row, "mp", 0, 0) or 0),
        "max_mp": int(_row_get(row, "max_mp", 1, 0) or 0),
    }


def set_user_mp(user_id: int, mp: int):
    legacy = _legacy_function("set_user_mp")
    if legacy:
        return legacy(user_id, mp)

    max_mp = get_max_mp(user_id)
    safe_mp = max(0, min(int(mp), int(max_mp)))
    _execute_commit("UPDATE users SET mp=? WHERE user_id=?", (safe_mp, user_id))
    return safe_mp


def get_max_mp(user_id: int):
    legacy = _legacy_function("get_max_mp")
    if legacy:
        return legacy(user_id)

    row = _fetchone("SELECT max_mp FROM users WHERE user_id=?", (user_id,))
    value = _row_get(row, "max_mp", 0, None)
    if value is not None:
        return int(value or 0)

    # Conservative fallback if max_mp is absent/empty.
    class_key = get_character_class(user_id)
    if class_key in ("mage", "priest"):
        return 100
    return 0


def refresh_user_mp(user_id: int):
    legacy = _legacy_function("refresh_user_mp")
    if legacy:
        return legacy(user_id)

    max_mp = get_max_mp(user_id)
    _execute_commit("UPDATE users SET mp=?, max_mp=? WHERE user_id=?", (max_mp, max_mp, user_id))
    return {"mp": max_mp, "max_mp": max_mp}


# Class reset sphere / class change availability wrappers.
# These keep existing behavior while moving API ownership into character_system.

def grant_class_change_available(user_id: int, amount: int = 1):
    legacy = _legacy_function("grant_class_change_available")
    if legacy:
        return legacy(user_id, amount)
    return False


def consume_class_change_available(user_id: int):
    legacy = _legacy_function("consume_class_change_available")
    if legacy:
        return legacy(user_id)
    return False


def get_class_change_available(user_id: int):
    legacy = _legacy_function("get_class_change_available")
    if legacy:
        return legacy(user_id)

    # Some project versions used has_class_change_available.
    legacy_alt = _legacy_function("has_class_change_available")
    if legacy_alt:
        return legacy_alt(user_id)

    return 0


def has_class_change_available(user_id: int):
    legacy = _legacy_function("has_class_change_available")
    if legacy:
        return legacy(user_id)
    return bool(get_class_change_available(user_id))


def get_class_reset_sphere_item_id():
    return int(_legacy_value("CLASS_RESET_SPHERE_ITEM_ID", CLASS_RESET_SPHERE_ITEM_ID))
'''

DB_APPEND = r'''

# ==============================
# ✅ ROM 9.0.1 CHARACTER SYSTEM FACADE WRAPPERS V1
# ==============================

# Safety approach:
# - preserve the current final db.py implementations as _legacy_* refs;
# - expose db.py functions as wrappers to systems.character_system;
# - systems.character_system calls legacy refs where available;
# - no gameplay behavior change intended.

try:
    _legacy_CLASS_CONFIGS_before_character_system_v1 = CLASS_CONFIGS
except NameError:
    _legacy_CLASS_CONFIGS_before_character_system_v1 = None

try:
    _legacy_CLASS_RESET_SPHERE_ITEM_ID_before_character_system_v1 = CLASS_RESET_SPHERE_ITEM_ID
except NameError:
    _legacy_CLASS_RESET_SPHERE_ITEM_ID_before_character_system_v1 = 301

for _name in [
    "normalize_character_name",
    "validate_character_name",
    "get_character_name",
    "set_character_name",
    "get_character_class",
    "set_character_class",
    "get_character_class_display",
    "get_character_resource_type",
    "get_user_mp",
    "set_user_mp",
    "get_max_mp",
    "refresh_user_mp",
    "grant_class_change_available",
    "consume_class_change_available",
    "get_class_change_available",
    "has_class_change_available",
]:
    if _name in globals() and f"_legacy_{_name}_before_character_system_v1" not in globals():
        globals()[f"_legacy_{_name}_before_character_system_v1"] = globals()[_name]


def _character_system_v1():
    from systems import character_system as _mod
    return _mod


def normalize_character_name(name):
    return _character_system_v1().normalize_character_name(name)


def validate_character_name(name):
    return _character_system_v1().validate_character_name(name)


def get_character_name(user_id):
    return _character_system_v1().get_character_name(user_id)


def set_character_name(user_id, name):
    return _character_system_v1().set_character_name(user_id, name)


def get_character_class(user_id):
    return _character_system_v1().get_character_class(user_id)


def set_character_class(user_id, class_key):
    return _character_system_v1().set_character_class(user_id, class_key)


def get_character_class_display(user_id):
    return _character_system_v1().get_character_class_display(user_id)


def get_character_resource_type(user_id):
    return _character_system_v1().get_character_resource_type(user_id)


def get_user_mp(user_id):
    return _character_system_v1().get_user_mp(user_id)


def set_user_mp(user_id, mp):
    return _character_system_v1().set_user_mp(user_id, mp)


def get_max_mp(user_id):
    return _character_system_v1().get_max_mp(user_id)


def refresh_user_mp(user_id):
    return _character_system_v1().refresh_user_mp(user_id)


def grant_class_change_available(user_id, amount=1):
    return _character_system_v1().grant_class_change_available(user_id, amount)


def consume_class_change_available(user_id):
    return _character_system_v1().consume_class_change_available(user_id)


def get_class_change_available(user_id):
    return _character_system_v1().get_class_change_available(user_id)


def has_class_change_available(user_id):
    return _character_system_v1().has_class_change_available(user_id)


try:
    CLASS_CONFIGS = _legacy_CLASS_CONFIGS_before_character_system_v1 or _character_system_v1().DEFAULT_CLASS_CONFIGS
except Exception:
    pass

try:
    CLASS_RESET_SPHERE_ITEM_ID = _character_system_v1().get_class_reset_sphere_item_id()
except Exception:
    pass
'''

TOOLS_PATCH = r'''

# 9.0.1 character system API
CHARACTER_API = [
    "normalize_character_name",
    "validate_character_name",
    "get_character_name",
    "set_character_name",
    "get_character_class",
    "set_character_class",
    "get_character_class_display",
    "get_character_resource_type",
    "get_user_mp",
    "set_user_mp",
    "get_max_mp",
    "refresh_user_mp",
]
'''


def make_backup(root: Path, target: Path) -> Path:
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def write_character_system(root: Path):
    target = root / CHARACTER_TARGET
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = None

    if target.exists():
        current = target.read_text(encoding="utf-8")
        if CHARACTER_MARKER in current:
            return target, None, False
        backup = make_backup(root, target)

    target.write_text(CHARACTER_CODE, encoding="utf-8")
    return target, backup, True


def append_db_wrappers(root: Path):
    target = root / DB_TARGET
    if not target.exists():
        raise SystemExit("❌ db.py не знайдено")

    current = target.read_text(encoding="utf-8")
    if DB_MARKER in current:
        return target, None, False

    backup = make_backup(root, target)
    target.write_text(current.rstrip() + "\n" + DB_APPEND + "\n", encoding="utf-8")
    return target, backup, True


def main():
    root = Path(__file__).resolve().parents[1]
    changed = []
    backups = []

    try:
        path, backup, did_change = write_character_system(root)
        if did_change:
            changed.append(path)
        if backup:
            backups.append(backup)

        path, backup, did_change = append_db_wrappers(root)
        if did_change:
            changed.append(path)
        if backup:
            backups.append(backup)

        py_compile.compile(str(root / CHARACTER_TARGET), doraise=True)
        py_compile.compile(str(root / DB_TARGET), doraise=True)

    except Exception as error:
        raise SystemExit(
            "❌ Помилка під час patch_9_0_1_character_system_extract.\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.1 Character System Extract застосовано успішно.")

    if changed:
        print("\nСтворено/оновлено:")
        for path in changed:
            print(f"- {path}")

    if backups:
        print("\nBackup:")
        for path in backups:
            print(f"- {path}")

    print("\nЩо зроблено:")
    print("- створено systems/character_system.py")
    print("- db.py отримав compatibility wrappers для character/class/MP API")
    print("- старі реалізації db.py збережені як _legacy_* refs")
    print("- behavior має залишитись без змін")

    print("\nПісля патча запусти:")
    print("python -m py_compile .\\systems\\character_system.py")
    print("python -m py_compile .\\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")


if __name__ == "__main__":
    main()
