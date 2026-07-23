from pathlib import Path
from datetime import datetime
import re
import py_compile

PATCH_NAME = "9_0_4_energy_system_extract"
MARKER = "# ✅ REFACTOR 9.0.4 ENERGY SYSTEM FACADE"

ENERGY_API_CANDIDATES = [
    # init / schema
    "init_energy_system",

    # common energy getters/setters that may exist in db.py
    "get_user_energy",
    "set_user_energy",
    "add_user_energy",
    "consume_user_energy",
    "restore_user_energy",
    "get_max_energy",
    "get_current_energy",
    "set_current_energy",
    "get_energy",
    "set_energy",
    "add_energy",
    "consume_energy",
    "restore_energy",

    # passive / exploration energy helpers
    "process_energy_regeneration",
    "process_energy_regen",
    "process_passive_energy_regeneration",
    "get_energy_regen_info",
    "get_energy_status",
    "reset_energy_if_needed",
    "update_energy_regen_timestamp",

    # combat energy helpers, if they are currently exposed from db.py
    "get_user_combat_energy",
    "set_user_combat_energy",
    "add_user_combat_energy",
    "consume_user_combat_energy",
    "restore_user_combat_energy",
]


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def find_top_level_defs(text):
    pattern = re.compile(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)
    return pattern.findall(text)


def build_energy_system_py(found_names):
    # The module intentionally calls legacy implementations through db.py.
    # This keeps behavior unchanged while moving the public domain API into systems/energy_system.py.
    lines = []
    lines.append('"""Energy system facade extracted from db.py in refactor 9.0.4.\n\n')
    lines.append('This module is intentionally conservative: it delegates to the legacy db.py implementations.\n')
    lines.append('Handlers can keep importing from db.py while db.py forwards calls here.\n')
    lines.append('Later phases may move the real implementation here after behavior is fully verified.\n')
    lines.append('"""\n\n')
    lines.append("from importlib import import_module\n\n\n")
    lines.append("def _db():\n")
    lines.append("    return import_module('db')\n\n\n")
    lines.append("def _call_legacy(function_name, *args, **kwargs):\n")
    lines.append("    db = _db()\n")
    lines.append("    legacy_name = f'_legacy_{function_name}_before_energy_system_v1'\n")
    lines.append("    legacy = getattr(db, legacy_name, None)\n")
    lines.append("    if legacy is None:\n")
    lines.append("        raise AttributeError(f'Legacy energy function not found: {legacy_name}')\n")
    lines.append("    return legacy(*args, **kwargs)\n\n\n")

    for name in ENERGY_API_CANDIDATES:
        if name in found_names:
            lines.append(f"def {name}(*args, **kwargs):\n")
            lines.append(f"    return _call_legacy('{name}', *args, **kwargs)\n\n\n")

    return "".join(lines).rstrip() + "\n"


def build_db_wrapper_block(found_names):
    lines = []
    lines.append("\n\n# ==============================\n")
    lines.append("# ✅ REFACTOR 9.0.4 ENERGY SYSTEM FACADE\n")
    lines.append("# ==============================\n\n")
    lines.append("def _energy_system_v1():\n")
    lines.append("    from systems import energy_system\n")
    lines.append("    return energy_system\n\n\n")

    for name in ENERGY_API_CANDIDATES:
        if name in found_names:
            lines.append(f"try:\n")
            lines.append(f"    _legacy_{name}_before_energy_system_v1 = {name}\n")
            lines.append(f"except NameError:\n")
            lines.append(f"    _legacy_{name}_before_energy_system_v1 = None\n\n")

    for name in ENERGY_API_CANDIDATES:
        if name in found_names:
            lines.append(f"def {name}(*args, **kwargs):\n")
            lines.append(f"    return _energy_system_v1().{name}(*args, **kwargs)\n\n\n")

    return "".join(lines).rstrip() + "\n"


def main():
    root = Path(__file__).resolve().parents[1]
    db_path = root / "db.py"
    systems_dir = root / "systems"
    energy_path = systems_dir / "energy_system.py"

    if not db_path.exists():
        raise SystemExit("❌ db.py не знайдено.")

    systems_dir.mkdir(exist_ok=True)

    db_text = db_path.read_text(encoding="utf-8")

    if MARKER in db_text:
        print("ℹ️ 9.0.4 energy facade уже є в db.py. Повторне застосування не потрібне.")
        return

    all_defs = find_top_level_defs(db_text)
    found_names = [name for name in ENERGY_API_CANDIDATES if name in all_defs]

    if not found_names:
        raise SystemExit(
            "❌ У db.py не знайдено жодної energy-функції з очікуваного списку.\n"
            "Нічого не змінено."
        )

    db_backup = make_backup(root, db_path)
    energy_backup = None
    if energy_path.exists():
        energy_backup = make_backup(root, energy_path)

    original_db = db_text
    original_energy = energy_path.read_text(encoding="utf-8") if energy_path.exists() else None

    try:
        energy_path.write_text(build_energy_system_py(set(found_names)), encoding="utf-8")
        db_path.write_text(db_text.rstrip() + build_db_wrapper_block(set(found_names)), encoding="utf-8")

        py_compile.compile(str(energy_path), doraise=True)
        py_compile.compile(str(db_path), doraise=True)

    except Exception as error:
        db_path.write_text(original_db, encoding="utf-8")
        if original_energy is None:
            if energy_path.exists():
                energy_path.unlink()
        else:
            energy_path.write_text(original_energy, encoding="utf-8")

        raise SystemExit(
            "❌ Помилка під час patch_9_0_4_energy_system_extract.\n"
            "Файли відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.4 Energy System Extract застосовано успішно.")
    print()
    print("Створено/оновлено:")
    print(f"- {energy_path}")
    print(f"- {db_path}")
    print()
    print("Backup:")
    print(f"- {db_backup}")
    if energy_backup:
        print(f"- {energy_backup}")
    print()
    print("Energy API, який перенесено у facade:")
    for name in found_names:
        print(f"- {name}")
    print()
    print("Що зроблено:")
    print("- створено systems/energy_system.py")
    print("- db.py отримав compatibility wrappers для energy API")
    print("- старі реалізації db.py збережені як _legacy_* refs")
    print("- behavior має залишитись без змін")
    print()
    print("Після патча запусти:")
    print("python -m py_compile .\\systems\\energy_system.py")
    print("python -m py_compile .\\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")


if __name__ == "__main__":
    main()
