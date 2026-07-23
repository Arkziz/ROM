from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_2_player_system_extract"
DB_TARGET = Path("db.py")
PLAYER_TARGET = Path("systems") / "player_system.py"
DB_MARKER = "# ✅ ROM 9.0.2 PLAYER SYSTEM FACADE WRAPPERS V1"
PLAYER_MARKER = "# ✅ ROM 9.0.2 PLAYER SYSTEM V1"

PLAYER_CODE = r'''# ✅ ROM 9.0.2 PLAYER SYSTEM V1
"""
ROM Player System v1.

Goal of 9.0.2:
- create a dedicated player/progression/stat domain module;
- move public player/stats/gold/exp/API ownership behind systems.player_system;
- keep db.py as compatibility facade for existing handlers;
- preserve current behavior by delegating to legacy db.py implementations where available.

This stage is conservative and intentionally does not delete old db.py code.
"""

from __future__ import annotations

from typing import Any, Callable, Optional


def _db_module():
    import db
    return db


def _legacy_function(name: str) -> Optional[Callable[..., Any]]:
    db = _db_module()
    return getattr(db, f"_legacy_{name}_before_player_system_v1", None)


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


def get_player_stats(user_id: int):
    legacy = _legacy_function("get_player_stats")
    if legacy:
        return legacy(user_id)

    row = _fetchone(
        """
        SELECT str, dex, int, wis, sta, level
        FROM users
        WHERE user_id=?
        """,
        (user_id,),
    )

    if not row:
        return None

    return (
        int(_row_get(row, "str", 0, 10) or 10),
        int(_row_get(row, "dex", 1, 10) or 10),
        int(_row_get(row, "int", 2, 10) or 10),
        int(_row_get(row, "wis", 3, 10) or 10),
        int(_row_get(row, "sta", 4, 10) or 10),
        int(_row_get(row, "level", 5, 1) or 1),
    )


def get_player_level(user_id: int):
    legacy = _legacy_function("get_player_level")
    if legacy:
        return legacy(user_id)

    row = _fetchone("SELECT level FROM users WHERE user_id=?", (user_id,))
    return int(_row_get(row, "level", 0, 1) or 1)


def get_wallet(user_id: int):
    legacy = _legacy_function("get_wallet")
    if legacy:
        return legacy(user_id)

    row = _fetchone("SELECT gold FROM users WHERE user_id=?", (user_id,))
    return float(_row_get(row, "gold", 0, 0) or 0)


def add_gold(user_id: int, amount):
    legacy = _legacy_function("add_gold")
    if legacy:
        return legacy(user_id, amount)

    current = get_wallet(user_id)
    new_value = current + float(amount)
    _execute_commit("UPDATE users SET gold=? WHERE user_id=?", (new_value, user_id))
    return new_value


def add_exp(user_id: int, amount):
    legacy = _legacy_function("add_exp")
    if legacy:
        return legacy(user_id, amount)

    row = _fetchone("SELECT exp FROM users WHERE user_id=?", (user_id,))
    current = int(_row_get(row, "exp", 0, 0) or 0)
    new_value = current + int(amount)
    _execute_commit("UPDATE users SET exp=? WHERE user_id=?", (new_value, user_id))
    return {"exp": new_value, "level": get_player_level(user_id), "level_ups": 0}


def add_kill(user_id: int, amount: int = 1):
    legacy = _legacy_function("add_kill")
    if legacy:
        return legacy(user_id, amount)

    try:
        _execute_commit(
            "UPDATE users SET kills=COALESCE(kills, 0)+? WHERE user_id=?",
            (int(amount), user_id),
        )
    except Exception:
        # Some older DB versions might use a different column name.
        return False
    return True


def get_user_progress(user_id: int):
    legacy = _legacy_function("get_user_progress")
    if legacy:
        return legacy(user_id)

    row = _fetchone(
        """
        SELECT level, exp, gold, kills
        FROM users
        WHERE user_id=?
        """,
        (user_id,),
    )

    if not row:
        return None

    return {
        "level": int(_row_get(row, "level", 0, 1) or 1),
        "exp": int(_row_get(row, "exp", 1, 0) or 0),
        "gold": float(_row_get(row, "gold", 2, 0) or 0),
        "kills": int(_row_get(row, "kills", 3, 0) or 0),
    }


def get_attack(user_id: int):
    legacy = _legacy_function("get_attack")
    if legacy:
        return legacy(user_id)

    stats = get_player_stats(user_id)
    if not stats:
        return 1
    str_, dex, int_, wis, sta, level = stats
    return max(1, int(str_))


def get_magic_attack(user_id: int):
    legacy = _legacy_function("get_magic_attack")
    if legacy:
        return legacy(user_id)

    stats = get_player_stats(user_id)
    if not stats:
        return 1
    str_, dex, int_, wis, sta, level = stats
    return max(1, int(int_))


def get_max_hp(user_id: int):
    legacy = _legacy_function("get_max_hp")
    if legacy:
        return legacy(user_id)

    stats = get_player_stats(user_id)
    if not stats:
        return 170
    str_, dex, int_, wis, sta, level = stats
    return int(120 + level * 10 + sta * 5)


def get_current_hp_raw(user_id: int):
    legacy = _legacy_function("get_current_hp_raw")
    if legacy:
        return legacy(user_id)

    row = _fetchone("SELECT hp FROM users WHERE user_id=?", (user_id,))
    return int(_row_get(row, "hp", 0, get_max_hp(user_id)) or get_max_hp(user_id))


def get_current_hp(user_id: int):
    legacy = _legacy_function("get_current_hp")
    if legacy:
        return legacy(user_id)
    return get_current_hp_raw(user_id)


def set_current_hp(user_id: int, hp: int):
    legacy = _legacy_function("set_current_hp")
    if legacy:
        return legacy(user_id, hp)

    max_hp = get_max_hp(user_id)
    safe_hp = max(0, min(int(hp), int(max_hp)))
    _execute_commit("UPDATE users SET hp=? WHERE user_id=?", (safe_hp, user_id))
    return safe_hp


def get_physical_defense(user_id: int):
    legacy = _legacy_function("get_physical_defense")
    if legacy:
        return legacy(user_id)

    stats = get_player_stats(user_id)
    if not stats:
        return 0
    str_, dex, int_, wis, sta, level = stats
    return int(sta * 0.2)


def get_magic_defense(user_id: int):
    legacy = _legacy_function("get_magic_defense")
    if legacy:
        return legacy(user_id)

    stats = get_player_stats(user_id)
    if not stats:
        return 0
    str_, dex, int_, wis, sta, level = stats
    return int(wis)


def get_physical_crit_chance_display(user_id: int):
    legacy = _legacy_function("get_physical_crit_chance_display")
    if legacy:
        return legacy(user_id)
    return 5.0


def get_magical_crit_chance_display(user_id: int):
    legacy = _legacy_function("get_magical_crit_chance_display")
    if legacy:
        return legacy(user_id)
    return 5.0


def get_base_dodge_chance_display(user_id: int):
    legacy = _legacy_function("get_base_dodge_chance_display")
    if legacy:
        return legacy(user_id)
    return 5.0
'''

DB_APPEND = r'''

# ==============================
# ✅ ROM 9.0.2 PLAYER SYSTEM FACADE WRAPPERS V1
# ==============================

# Safety approach:
# - preserve the current final db.py implementations as _legacy_* refs;
# - expose db.py player/stat/progression API as wrappers to systems.player_system;
# - systems.player_system calls legacy refs where available;
# - no gameplay behavior change intended.

for _name in [
    "get_player_stats",
    "get_player_level",
    "add_exp",
    "add_gold",
    "add_kill",
    "get_wallet",
    "get_user_progress",
    "get_attack",
    "get_magic_attack",
    "get_max_hp",
    "get_current_hp_raw",
    "get_current_hp",
    "set_current_hp",
    "get_physical_defense",
    "get_magic_defense",
    "get_physical_crit_chance_display",
    "get_magical_crit_chance_display",
    "get_base_dodge_chance_display",
]:
    if _name in globals() and f"_legacy_{_name}_before_player_system_v1" not in globals():
        globals()[f"_legacy_{_name}_before_player_system_v1"] = globals()[_name]


def _player_system_v1():
    from systems import player_system as _mod
    return _mod


def get_player_stats(user_id):
    return _player_system_v1().get_player_stats(user_id)


def get_player_level(user_id):
    return _player_system_v1().get_player_level(user_id)


def add_exp(user_id, amount):
    return _player_system_v1().add_exp(user_id, amount)


def add_gold(user_id, amount):
    return _player_system_v1().add_gold(user_id, amount)


def add_kill(user_id, amount=1):
    return _player_system_v1().add_kill(user_id, amount)


def get_wallet(user_id):
    return _player_system_v1().get_wallet(user_id)


def get_user_progress(user_id):
    return _player_system_v1().get_user_progress(user_id)


def get_attack(user_id):
    return _player_system_v1().get_attack(user_id)


def get_magic_attack(user_id):
    return _player_system_v1().get_magic_attack(user_id)


def get_max_hp(user_id):
    return _player_system_v1().get_max_hp(user_id)


def get_current_hp_raw(user_id):
    return _player_system_v1().get_current_hp_raw(user_id)


def get_current_hp(user_id):
    return _player_system_v1().get_current_hp(user_id)


def set_current_hp(user_id, hp):
    return _player_system_v1().set_current_hp(user_id, hp)


def get_physical_defense(user_id):
    return _player_system_v1().get_physical_defense(user_id)


def get_magic_defense(user_id):
    return _player_system_v1().get_magic_defense(user_id)


def get_physical_crit_chance_display(user_id):
    return _player_system_v1().get_physical_crit_chance_display(user_id)


def get_magical_crit_chance_display(user_id):
    return _player_system_v1().get_magical_crit_chance_display(user_id)


def get_base_dodge_chance_display(user_id):
    return _player_system_v1().get_base_dodge_chance_display(user_id)
'''


def make_backup(root: Path, target: Path) -> Path:
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def write_player_system(root: Path):
    target = root / PLAYER_TARGET
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = None

    if target.exists():
        current = target.read_text(encoding="utf-8")
        if PLAYER_MARKER in current:
            return target, None, False
        backup = make_backup(root, target)

    target.write_text(PLAYER_CODE, encoding="utf-8")
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
        path, backup, did_change = write_player_system(root)
        if did_change:
            changed.append(path)
        if backup:
            backups.append(backup)

        path, backup, did_change = append_db_wrappers(root)
        if did_change:
            changed.append(path)
        if backup:
            backups.append(backup)

        py_compile.compile(str(root / PLAYER_TARGET), doraise=True)
        py_compile.compile(str(root / DB_TARGET), doraise=True)

    except Exception as error:
        raise SystemExit(
            "❌ Помилка під час patch_9_0_2_player_system_extract.\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.2 Player System Extract застосовано успішно.")

    if changed:
        print("\nСтворено/оновлено:")
        for path in changed:
            print(f"- {path}")

    if backups:
        print("\nBackup:")
        for path in backups:
            print(f"- {path}")

    print("\nЩо зроблено:")
    print("- створено systems/player_system.py")
    print("- db.py отримав compatibility wrappers для player/stats/progression API")
    print("- старі реалізації db.py збережені як _legacy_* refs")
    print("- behavior має залишитись без змін")

    print("\nПісля патча запусти:")
    print("python -m py_compile .\\systems\\player_system.py")
    print("python -m py_compile .\\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")


if __name__ == "__main__":
    main()
