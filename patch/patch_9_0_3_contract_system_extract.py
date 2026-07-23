from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_3_contract_system_extract"
DB_TARGET = Path("db.py")
CONTRACT_TARGET = Path("systems") / "contract_system.py"
DB_MARKER = "# ✅ ROM 9.0.3 CONTRACT SYSTEM FACADE WRAPPERS V1"
CONTRACT_MARKER = "# ✅ ROM 9.0.3 CONTRACT SYSTEM V1"

CONTRACT_CODE = r'''# ✅ ROM 9.0.3 CONTRACT SYSTEM V1
"""
ROM Contract System v1.

Goal of 9.0.3:
- create a dedicated contract domain module;
- move contract public API ownership behind systems.contract_system;
- keep db.py as compatibility facade for existing handlers/systems;
- preserve existing behavior by delegating to legacy db.py implementations where available.

Important:
- This patch does NOT delete old db.py contract code.
- This patch intentionally uses *args/**kwargs for some functions because older code may
  call contract helpers with slightly different signatures.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional


DEFAULT_CONTRACT_TARGET_KILLS = 5


def _db_module():
    import db
    return db


def _legacy_function(name: str) -> Optional[Callable[..., Any]]:
    db = _db_module()
    return getattr(db, f"_legacy_{name}_before_contract_system_v1", None)


def _legacy_value(name: str, default: Any = None) -> Any:
    db = _db_module()
    return getattr(db, f"_legacy_{name}_before_contract_system_v1", default)


def _fetchone(sql: str, params: tuple = ()):  # sqlite3.Row or tuple depending on project state
    db = _db_module()
    db.cursor.execute(sql, params)
    return db.cursor.fetchone()


def _fetchall(sql: str, params: tuple = ()):  # sqlite3.Row or tuple depending on project state
    db = _db_module()
    db.cursor.execute(sql, params)
    return db.cursor.fetchall()


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


def get_contract_target_kills() -> int:
    return int(_legacy_value("CONTRACT_TARGET_KILLS", DEFAULT_CONTRACT_TARGET_KILLS) or DEFAULT_CONTRACT_TARGET_KILLS)


CONTRACT_TARGET_KILLS = get_contract_target_kills()


def get_today_str(*args, **kwargs):
    legacy = _legacy_function("get_today_str")
    if legacy:
        return legacy(*args, **kwargs)
    return datetime.now().strftime("%Y-%m-%d")


def init_contract_system(*args, **kwargs):
    legacy = _legacy_function("init_contract_system")
    if legacy:
        return legacy(*args, **kwargs)

    # Conservative fallback: do nothing if legacy initializer does not exist.
    return True


def create_daily_contract(*args, **kwargs):
    legacy = _legacy_function("create_daily_contract")
    if legacy:
        return legacy(*args, **kwargs)
    return None


def get_active_contract(*args, **kwargs):
    legacy = _legacy_function("get_active_contract")
    if legacy:
        return legacy(*args, **kwargs)
    return None


def get_contract_status(*args, **kwargs):
    legacy = _legacy_function("get_contract_status")
    if legacy:
        return legacy(*args, **kwargs)

    return {
        "has_contract": False,
        "message": "Контракт не знайдено.",
    }


def process_contract_progress_on_kill(*args, **kwargs):
    legacy = _legacy_function("process_contract_progress_on_kill")
    if legacy:
        return legacy(*args, **kwargs)

    return {
        "updated": False,
        "completed": False,
        "message": "",
    }


def claim_contract_reward(*args, **kwargs):
    legacy = _legacy_function("claim_contract_reward")
    if legacy:
        return legacy(*args, **kwargs)

    return {
        "success": False,
        "message": "❌ Немає завершеного контракту для отримання нагороди.",
    }


def get_daily_contract_reset_info(*args, **kwargs):
    legacy = _legacy_function("get_daily_contract_reset_info")
    if legacy:
        return legacy(*args, **kwargs)

    return {
        "today": get_today_str(),
    }


def reset_daily_contracts_if_needed(*args, **kwargs):
    legacy = _legacy_function("reset_daily_contracts_if_needed")
    if legacy:
        return legacy(*args, **kwargs)
    return False


def get_contract_mobs_equivalent(*args, **kwargs):
    legacy = _legacy_function("get_contract_mobs_equivalent")
    if legacy:
        return legacy(*args, **kwargs)
    return get_contract_target_kills()


def migrate_contract_target_kills_to_v2(*args, **kwargs):
    legacy = _legacy_function("migrate_contract_target_kills_to_v2")
    if legacy:
        return legacy(*args, **kwargs)
    return False
'''

DB_APPEND = r'''

# ==============================
# ✅ ROM 9.0.3 CONTRACT SYSTEM FACADE WRAPPERS V1
# ==============================

# Safety approach:
# - preserve the current final db.py contract implementations as _legacy_* refs;
# - expose db.py contract API as wrappers to systems.contract_system;
# - systems.contract_system calls legacy refs where available;
# - no gameplay behavior change intended.

try:
    _legacy_CONTRACT_TARGET_KILLS_before_contract_system_v1 = CONTRACT_TARGET_KILLS
except NameError:
    _legacy_CONTRACT_TARGET_KILLS_before_contract_system_v1 = 5

try:
    _legacy_CONTRACT_MOBS_EQUIVALENT_before_contract_system_v1 = CONTRACT_MOBS_EQUIVALENT
except NameError:
    _legacy_CONTRACT_MOBS_EQUIVALENT_before_contract_system_v1 = 5

for _name in [
    "get_today_str",
    "init_contract_system",
    "create_daily_contract",
    "get_active_contract",
    "get_contract_status",
    "process_contract_progress_on_kill",
    "claim_contract_reward",
    "get_daily_contract_reset_info",
    "reset_daily_contracts_if_needed",
    "get_contract_mobs_equivalent",
    "migrate_contract_target_kills_to_v2",
]:
    if _name in globals() and f"_legacy_{_name}_before_contract_system_v1" not in globals():
        globals()[f"_legacy_{_name}_before_contract_system_v1"] = globals()[_name]


def _contract_system_v1():
    from systems import contract_system as _mod
    return _mod


def get_today_str(*args, **kwargs):
    return _contract_system_v1().get_today_str(*args, **kwargs)


def init_contract_system(*args, **kwargs):
    return _contract_system_v1().init_contract_system(*args, **kwargs)


def create_daily_contract(*args, **kwargs):
    return _contract_system_v1().create_daily_contract(*args, **kwargs)


def get_active_contract(*args, **kwargs):
    return _contract_system_v1().get_active_contract(*args, **kwargs)


def get_contract_status(*args, **kwargs):
    return _contract_system_v1().get_contract_status(*args, **kwargs)


def process_contract_progress_on_kill(*args, **kwargs):
    return _contract_system_v1().process_contract_progress_on_kill(*args, **kwargs)


def claim_contract_reward(*args, **kwargs):
    return _contract_system_v1().claim_contract_reward(*args, **kwargs)


def get_daily_contract_reset_info(*args, **kwargs):
    return _contract_system_v1().get_daily_contract_reset_info(*args, **kwargs)


def reset_daily_contracts_if_needed(*args, **kwargs):
    return _contract_system_v1().reset_daily_contracts_if_needed(*args, **kwargs)


def get_contract_mobs_equivalent(*args, **kwargs):
    return _contract_system_v1().get_contract_mobs_equivalent(*args, **kwargs)


def migrate_contract_target_kills_to_v2(*args, **kwargs):
    return _contract_system_v1().migrate_contract_target_kills_to_v2(*args, **kwargs)


try:
    CONTRACT_TARGET_KILLS = _contract_system_v1().get_contract_target_kills()
except Exception:
    pass

try:
    CONTRACT_MOBS_EQUIVALENT = _contract_system_v1().get_contract_mobs_equivalent()
except Exception:
    pass
'''


def make_backup(root: Path, target: Path) -> Path:
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def write_contract_system(root: Path):
    target = root / CONTRACT_TARGET
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = None

    if target.exists():
        current = target.read_text(encoding="utf-8")
        if CONTRACT_MARKER in current:
            return target, None, False
        backup = make_backup(root, target)

    target.write_text(CONTRACT_CODE, encoding="utf-8")
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
        path, backup, did_change = write_contract_system(root)
        if did_change:
            changed.append(path)
        if backup:
            backups.append(backup)

        path, backup, did_change = append_db_wrappers(root)
        if did_change:
            changed.append(path)
        if backup:
            backups.append(backup)

        py_compile.compile(str(root / CONTRACT_TARGET), doraise=True)
        py_compile.compile(str(root / DB_TARGET), doraise=True)

    except Exception as error:
        raise SystemExit(
            "❌ Помилка під час patch_9_0_3_contract_system_extract.\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.3 Contract System Extract застосовано успішно.")

    if changed:
        print("\nСтворено/оновлено:")
        for path in changed:
            print(f"- {path}")

    if backups:
        print("\nBackup:")
        for path in backups:
            print(f"- {path}")

    print("\nЩо зроблено:")
    print("- створено systems/contract_system.py")
    print("- db.py отримав compatibility wrappers для contract API")
    print("- старі реалізації db.py збережені як _legacy_* refs")
    print("- wrappers використовують *args/**kwargs для сумісності сигнатур")
    print("- behavior має залишитись без змін")

    print("\nПісля патча запусти:")
    print("python -m py_compile .\\systems\\contract_system.py")
    print("python -m py_compile .\\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")


if __name__ == "__main__":
    main()
