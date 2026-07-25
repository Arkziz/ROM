# ✅ ROM 9.0.3 CONTRACT SYSTEM V1
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
