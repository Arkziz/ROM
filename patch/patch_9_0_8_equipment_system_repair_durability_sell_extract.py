from pathlib import Path
from datetime import datetime
import ast
import py_compile

PATCH_NAME = "9_0_8_equipment_system_repair_durability_sell_extract"
MARKER = "# ✅ REFACTOR 9.0.8: EQUIPMENT SYSTEM REPAIR DURABILITY SELL FACADE"
EQUIPMENT_MARKER = "# ✅ REFACTOR 9.0.8: EQUIPMENT REPAIR DURABILITY SELL API"

WRITE_FUNCTION_CANDIDATES = [
    # repair write actions
    "repair_equipped_item",
    "repair_all_equipped",
    "get_repair_cost",
    "calculate_repair_cost",

    # durability / wear / death durability actions
    "damage_equipped_items_on_death",
    "damage_equipped_items",
    "apply_equipment_wear",
    "apply_equipment_wear_after_combat",
    "roll_equipment_wear_after_combat",
    "reduce_equipped_item_durability",
    "set_inventory_item_durability",
    "repair_inventory_item",

    # sell / trader write actions related to equipment and inventory
    "sell_inventory_item_to_trader",
    "sell_equipment_item_to_trader",
    "get_sell_price_for_inventory_item",
    "buy_common_equipment_from_trader",
    "buy_item_for_gold",
]


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


def build_equipment_append(found_names):
    lines = []
    lines.append("")
    lines.append(EQUIPMENT_MARKER)
    lines.append("# Repair/durability/sell wrappers. These delegate to legacy db.py implementations")
    lines.append("# and synchronize dynamic max HP after operations that can affect equipped bonuses.")
    lines.append("")
    lines.append("def _call_legacy_repair_durability_sell(name, *args, **kwargs):")
    lines.append("    db = _db()")
    lines.append("    legacy_name = f'_legacy_equipment_rds_v1_{name}'")
    lines.append("    legacy = getattr(db, legacy_name, None)")
    lines.append("    if legacy is None:")
    lines.append("        legacy = getattr(db, f'_legacy_equipment_write_v1_{name}', None)")
    lines.append("    if legacy is None:")
    lines.append("        legacy = getattr(db, f'_legacy_equipment_ro_v1_{name}', None)")
    lines.append("    if legacy is None:")
    lines.append("        raise AttributeError(f'Legacy equipment repair/durability/sell function not found: {legacy_name}')")
    lines.append("    return legacy(*args, **kwargs)")
    lines.append("")
    lines.append("def _extract_user_id_for_rds(args, kwargs):")
    lines.append("    if 'user_id' in kwargs:")
    lines.append("        return kwargs.get('user_id')")
    lines.append("    if args:")
    lines.append("        return args[0]")
    lines.append("    return None")
    lines.append("")
    lines.append("def _sync_hp_after_rds(user_id):")
    lines.append("    if user_id is None:")
    lines.append("        return None")
    lines.append("    try:")
    lines.append("        db = _db()")
    lines.append("        sync = getattr(db, 'sync_user_max_hp', None)")
    lines.append("        if sync:")
    lines.append("            try:")
    lines.append("                return sync(user_id, heal_to_full=False)")
    lines.append("            except TypeError:")
    lines.append("                return sync(user_id)")
    lines.append("    except Exception:")
    lines.append("        return None")
    lines.append("    return None")
    lines.append("")

    for name in found_names:
        lines.append(f"def {name}(*args, **kwargs):")
        lines.append("    user_id = _extract_user_id_for_rds(args, kwargs)")
        lines.append("    result = _call_legacy_repair_durability_sell('%s', *args, **kwargs)" % name)
        # Sync after functions that can change durability-equipped bonuses or inventory state.
        if name in {
            "repair_equipped_item", "repair_all_equipped", "repair_inventory_item",
            "damage_equipped_items_on_death", "damage_equipped_items", "apply_equipment_wear",
            "apply_equipment_wear_after_combat", "roll_equipment_wear_after_combat",
            "reduce_equipped_item_durability", "set_inventory_item_durability",
            "sell_inventory_item_to_trader", "sell_equipment_item_to_trader",
            "buy_common_equipment_from_trader", "buy_item_for_gold",
        }:
            lines.append("    _sync_hp_after_rds(user_id)")
        lines.append("    return result")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def append_equipment_system(root, found_names):
    target = root / "systems" / "equipment_system.py"
    if not target.exists():
        raise SystemExit("❌ systems/equipment_system.py не знайдено. Спочатку потрібен 9.0.6.")

    original = target.read_text(encoding="utf-8")
    if EQUIPMENT_MARKER in original:
        print("ℹ️ systems/equipment_system.py вже має 9.0.8 block. Пропускаю.")
        return None, original

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + build_equipment_append(found_names), encoding="utf-8")
    return backup, original


def patch_db(root, found_names):
    target = root / "db.py"
    if not target.exists():
        raise SystemExit("❌ db.py не знайдено.")

    original = target.read_text(encoding="utf-8")
    if MARKER in original:
        print("ℹ️ db.py вже має REFACTOR 9.0.8 block. Пропускаю db.py.")
        return None, original

    backup = make_backup(root, target)

    lines = []
    lines.append("")
    lines.append(MARKER)
    lines.append("# This block keeps db.py as public compatibility facade.")
    lines.append("# Actual equipment repair/durability/sell domain entrypoint: systems/equipment_system.py")
    lines.append("")
    lines.append("def _equipment_system_rds_v1():")
    lines.append("    from systems import equipment_system")
    lines.append("    return equipment_system")
    lines.append("")

    for name in found_names:
        legacy_name = f"_legacy_equipment_rds_v1_{name}"
        lines.append("try:")
        lines.append(f"    {legacy_name}")
        lines.append("except NameError:")
        lines.append(f"    {legacy_name} = {name}")
        lines.append("")

    for name in found_names:
        lines.append(f"def {name}(*args, **kwargs):")
        lines.append(f"    return _equipment_system_rds_v1().{name}(*args, **kwargs)")
        lines.append("")

    patched = original.rstrip() + "\n" + "\n".join(lines) + "\n"
    target.write_text(patched, encoding="utf-8")
    return backup, original


def main():
    root = Path(__file__).resolve().parents[1]
    db_path = root / "db.py"
    equipment_path = root / "systems" / "equipment_system.py"

    if not db_path.exists():
        raise SystemExit("❌ db.py не знайдено.")
    if not equipment_path.exists():
        raise SystemExit("❌ systems/equipment_system.py не знайдено. Спочатку застосуй 9.0.6.")

    db_original = db_path.read_text(encoding="utf-8")
    equipment_original = equipment_path.read_text(encoding="utf-8")

    defined = set(get_defined_functions(db_original))
    found_names = [name for name in WRITE_FUNCTION_CANDIDATES if name in defined]

    if not found_names:
        raise SystemExit("❌ Не знайдено repair/durability/sell-функцій у db.py для wrapper-ів.")

    changed_files = []
    backups = []

    try:
        equipment_backup, _ = append_equipment_system(root, found_names)
        if equipment_backup:
            backups.append(equipment_backup)
            changed_files.append(equipment_path)

        db_backup, _ = patch_db(root, found_names)
        if db_backup:
            backups.append(db_backup)
            changed_files.append(db_path)

        py_compile.compile(str(equipment_path), doraise=True)
        py_compile.compile(str(db_path), doraise=True)

    except Exception as error:
        db_path.write_text(db_original, encoding="utf-8")
        equipment_path.write_text(equipment_original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка під час patch_9_0_8_equipment_system_repair_durability_sell_extract.\n"
            "db.py і systems/equipment_system.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.8 Equipment System Repair/Durability/Sell Extract застосовано успішно.")
    print()
    print("Змінено:")
    for path in changed_files:
        print(f"- {path}")

    if backups:
        print()
        print("Backup:")
        for path in backups:
            print(f"- {path}")

    print()
    print("Equipment repair/durability/sell API перенесено у facade:")
    for name in found_names:
        print(f"- {name}")

    print()
    print("Що зроблено:")
    print("- db.py отримав compatibility wrappers для repair/durability/sell API")
    print("- systems/equipment_system.py отримав repair/durability/sell wrappers")
    print("- старі реалізації db.py збережені як _legacy_equipment_rds_v1_* refs")
    print("- після repair/durability/sell операцій синхронізується dynamic max HP, якщо доречно")
    print("- це завершує equipment facade у межах read/write без видалення старого коду")
    print()
    print("Після патча запусти:")
    print("python -m py_compile .\\systems\\equipment_system.py")
    print("python -m py_compile .\\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")


if __name__ == "__main__":
    main()
