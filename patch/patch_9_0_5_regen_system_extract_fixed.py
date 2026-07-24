from pathlib import Path
from datetime import datetime
import ast
import py_compile

PATCH_NAME = "9_0_5_regen_system_extract_fixed"
MARKER = "# ✅ REFACTOR 9.0.5: REGEN SYSTEM FACADE"

REGEN_FUNCTION_CANDIDATES = [
    "init_hp_regen_system",
    "init_passive_regen_system",
    "process_passive_regeneration",
    "reset_hp_regen_timers_now",
    "apply_passive_hp_regen",
    "apply_passive_mp_regen",
    "process_hp_regeneration",
    "process_mp_regeneration",
    "get_hp_regen_status",
    "get_mp_regen_status",
]

REGEN_SYSTEM_CODE = '''"""
ROM Regen System
================

Refactor 9.0.5 compatibility module.

This module is intentionally conservative:
- db.py remains the public compatibility facade for handlers.
- legacy implementations are kept in db.py as _legacy_regen_v1_* references.
- this module delegates to those legacy implementations.

Important HP rules:
- dynamic max HP from equipment/refine must be respected;
- equipping/refining armor must not heal the player automatically;
- passive regeneration may heal up to dynamic max HP;
- if max HP decreases, current HP must be clamped to the new max.
"""


def _db():
    import db
    return db


def _call_legacy(name, *args, **kwargs):
    db = _db()
    legacy_name = f"_legacy_regen_v1_{name}"
    legacy = getattr(db, legacy_name, None)

    if legacy is None:
        raise AttributeError(f"Legacy regen function not found: {legacy_name}")

    return legacy(*args, **kwargs)


def _sync_hp_if_possible(user_id):
    if user_id is None:
        return None

    db = _db()
    sync = getattr(db, "sync_user_max_hp", None)

    if not sync:
        return None

    try:
        return sync(user_id, heal_to_full=False)
    except TypeError:
        return sync(user_id)
    except Exception:
        return None


def init_hp_regen_system(*args, **kwargs):
    return _call_legacy("init_hp_regen_system", *args, **kwargs)


def init_passive_regen_system(*args, **kwargs):
    return _call_legacy("init_passive_regen_system", *args, **kwargs)


def reset_hp_regen_timers_now(user_id, *args, **kwargs):
    result = _call_legacy("reset_hp_regen_timers_now", user_id, *args, **kwargs)
    _sync_hp_if_possible(user_id)
    return result


def process_passive_regeneration(user_id, *args, **kwargs):
    """
    Passive regeneration wrapper.

    Before and after legacy regeneration, sync max HP against dynamic equipment/refine bonuses.
    This protects cases where armor refine changes max HP while users.max_hp is stale.
    """

    _sync_hp_if_possible(user_id)
    result = _call_legacy("process_passive_regeneration", user_id, *args, **kwargs)
    _sync_hp_if_possible(user_id)
    return result


def apply_passive_hp_regen(user_id, *args, **kwargs):
    _sync_hp_if_possible(user_id)
    result = _call_legacy("apply_passive_hp_regen", user_id, *args, **kwargs)
    _sync_hp_if_possible(user_id)
    return result


def apply_passive_mp_regen(*args, **kwargs):
    return _call_legacy("apply_passive_mp_regen", *args, **kwargs)


def process_hp_regeneration(user_id, *args, **kwargs):
    _sync_hp_if_possible(user_id)
    result = _call_legacy("process_hp_regeneration", user_id, *args, **kwargs)
    _sync_hp_if_possible(user_id)
    return result


def process_mp_regeneration(*args, **kwargs):
    return _call_legacy("process_mp_regeneration", *args, **kwargs)


def get_hp_regen_status(*args, **kwargs):
    return _call_legacy("get_hp_regen_status", *args, **kwargs)


def get_mp_regen_status(*args, **kwargs):
    return _call_legacy("get_mp_regen_status", *args, **kwargs)
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def get_defined_functions(text):
    tree = ast.parse(text)
    result = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            result.append(node.name)
    return result


def write_regen_system(root):
    systems_dir = root / "systems"
    systems_dir.mkdir(exist_ok=True)
    target = systems_dir / "regen_system.py"

    backup = None
    if target.exists():
        backup = make_backup(root, target)

    target.write_text(REGEN_SYSTEM_CODE, encoding="utf-8")
    return target, backup


def patch_db(root):
    target = root / "db.py"
    if not target.exists():
        raise SystemExit("❌ db.py не знайдено.")

    original = target.read_text(encoding="utf-8")
    if MARKER in original:
        print("ℹ️ db.py вже має REFACTOR 9.0.5 block. Пропускаю db.py.")
        return None, original

    defined = set(get_defined_functions(original))
    candidates = [name for name in REGEN_FUNCTION_CANDIDATES if name in defined]

    if not candidates:
        raise SystemExit("❌ Не знайдено жодної regen-функції в db.py для wrapper-ів.")

    backup = make_backup(root, target)

    lines = []
    lines.append("")
    lines.append(MARKER)
    lines.append("# This block keeps db.py as public compatibility facade.")
    lines.append("# Actual domain entrypoint: systems/regen_system.py")
    lines.append("")
    lines.append("def _regen_system_v1():")
    lines.append("    from systems import regen_system")
    lines.append("    return regen_system")
    lines.append("")

    for name in candidates:
        legacy_name = f"_legacy_regen_v1_{name}"
        lines.append("try:")
        lines.append(f"    {legacy_name}")
        lines.append("except NameError:")
        lines.append(f"    {legacy_name} = {name}")
        lines.append("")

    for name in candidates:
        lines.append(f"def {name}(*args, **kwargs):")
        lines.append(f"    return _regen_system_v1().{name}(*args, **kwargs)")
        lines.append("")

    patched = original.rstrip() + "\n" + "\n".join(lines) + "\n"
    target.write_text(patched, encoding="utf-8")
    return backup, original


def patch_tools_check_imports(root):
    target = root / "tools" / "check_imports.py"
    if not target.exists():
        return None

    text = target.read_text(encoding="utf-8")
    changed = False

    if '"systems/regen_system.py"' not in text and "'systems/regen_system.py'" not in text:
        marker = '"systems/refine_system.py",'
        if marker in text:
            text = text.replace(marker, marker + '\n    "systems/regen_system.py",')
            changed = True

    if '"systems.regen_system"' not in text and "'systems.regen_system'" not in text:
        marker = '"systems.refine_system",'
        if marker in text:
            text = text.replace(marker, marker + '\n    "systems.regen_system",')
            changed = True

    if changed:
        backup = make_backup(root, target)
        target.write_text(text, encoding="utf-8")
        return backup

    return None


def main():
    root = Path(__file__).resolve().parents[1]

    db_path = root / "db.py"
    if not db_path.exists():
        raise SystemExit("❌ db.py не знайдено.")

    db_original = db_path.read_text(encoding="utf-8")
    regen_path = root / "systems" / "regen_system.py"
    regen_original = regen_path.read_text(encoding="utf-8") if regen_path.exists() else None

    changed_files = []
    backups = []

    try:
        regen_path, regen_backup = write_regen_system(root)
        changed_files.append(regen_path)
        if regen_backup:
            backups.append(regen_backup)

        db_backup, _ = patch_db(root)
        if db_backup:
            backups.append(db_backup)
            changed_files.append(db_path)

        tools_backup = patch_tools_check_imports(root)
        if tools_backup:
            backups.append(tools_backup)
            changed_files.append(root / "tools" / "check_imports.py")

        py_compile.compile(str(root / "systems" / "regen_system.py"), doraise=True)
        py_compile.compile(str(db_path), doraise=True)
        if (root / "tools" / "check_imports.py").exists():
            py_compile.compile(str(root / "tools" / "check_imports.py"), doraise=True)

    except Exception as error:
        db_path.write_text(db_original, encoding="utf-8")
        if regen_original is None:
            if regen_path.exists():
                regen_path.unlink()
        else:
            regen_path.write_text(regen_original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка під час patch_9_0_5_regen_system_extract_fixed.\n"
            "db.py і systems/regen_system.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.5 Regen System Extract FIXED застосовано успішно.")
    print()
    print("Створено/оновлено:")
    for path in changed_files:
        print(f"- {path}")

    if backups:
        print()
        print("Backup:")
        for path in backups:
            print(f"- {path}")

    print()
    print("Що зроблено:")
    print("- створено systems/regen_system.py")
    print("- db.py отримав compatibility wrappers для regen API")
    print("- старі реалізації db.py збережені як _legacy_regen_v1_* refs")
    print("- process_passive_regeneration синхронізує dynamic max HP через sync_user_max_hp()")
    print("- tools/check_imports.py оновлено для systems.regen_system, якщо можливо")
    print()
    print("Після патча запусти:")
    print("python -m py_compile .\\systems\\regen_system.py")
    print("python -m py_compile .\\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")


if __name__ == "__main__":
    main()
