from pathlib import Path
from datetime import datetime
import ast
import py_compile
import shutil
import subprocess
import sys

PATCH_NAME = "9_0_12i1_legacy_cleanup_audit_and_safe_capture_removal"

# These equipment APIs now have final direct implementations in
# systems/equipment_system.py. The three class-compatibility readers are
# intentionally NOT included because they can still use the old read-only bridge.
SAFE_LEGACY_NAMES = {
    "_legacy_equipment_ro_v1_ensure_equipment_slots",
    "_legacy_equipment_ro_v1_get_all_equipped_items",
    "_legacy_equipment_ro_v1_get_equipped_items_for_repair",
    "_legacy_equipment_ro_v1_get_inventory_detailed",
    "_legacy_equipment_ro_v1_get_inventory_entry",
    "_legacy_equipment_ro_v1_get_item_by_inventory_id",
    "_legacy_equipment_ro_v1_get_item_by_inventory_id_full",
    "_legacy_equipment_ro_v1_get_item_bonuses",
    "_legacy_equipment_ro_v1_get_equipped_item_defenses",
    "_legacy_equipment_ro_v1_get_sellable_equipment_items",
    "_legacy_equipment_ro_v1_init_weapon_damage_system",
    "_legacy_equipment_ro_v1_calculate_weapon_damage_by_values",
    "_legacy_equipment_ro_v1_get_weapon_damage_by_inventory_id",
    "_legacy_equipment_ro_v1_get_inventory_weapon_damage_display",
    "_legacy_equipment_ro_v1_get_inventory_refine_level",
    "_legacy_equipment_ro_v1_get_inventory_refined_display_name",
    "_legacy_equipment_ro_v1_format_refined_item_name",
    "_legacy_equipment_write_v1_equip_inventory_item",
    "_legacy_equipment_write_v1_unequip_inventory_item",
    "_legacy_equipment_write_v1_unequip_incompatible_items_after_class_change",
    "_legacy_equipment_rds_v1_repair_equipped_item",
    "_legacy_equipment_rds_v1_repair_all_equipped",
    "_legacy_equipment_rds_v1_calculate_repair_cost",
    "_legacy_equipment_rds_v1_damage_equipped_items_on_death",
    "_legacy_equipment_rds_v1_sell_inventory_item_to_trader",
    "_legacy_equipment_rds_v1_buy_common_equipment_from_trader",
    "_legacy_equipment_rds_v1_buy_item_for_gold",
}

# Public final functions that must exist in equipment_system.py before cleanup.
REQUIRED_DIRECT_FUNCTIONS = {
    "ensure_equipment_slots",
    "get_all_equipped_items",
    "get_equipped_items_for_repair",
    "get_inventory_detailed",
    "get_inventory_entry",
    "get_item_by_inventory_id",
    "get_item_by_inventory_id_full",
    "get_item_bonuses",
    "get_equipped_item_defenses",
    "get_sellable_equipment_items",
    "init_weapon_damage_system",
    "calculate_weapon_damage_by_values",
    "get_weapon_damage_by_inventory_id",
    "get_inventory_weapon_damage_display",
    "get_inventory_refine_level",
    "get_inventory_refined_display_name",
    "format_refined_item_name",
    "equip_inventory_item",
    "unequip_inventory_item",
    "unequip_incompatible_items_after_class_change",
    "repair_equipped_item",
    "repair_all_equipped",
    "calculate_repair_cost",
    "damage_equipped_items_on_death",
    "sell_inventory_item_to_trader",
    "buy_common_equipment_from_trader",
    "buy_item_for_gold",
}


def backup_file(root, path):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = str(path.relative_to(root)).replace("\\", "_").replace("/", "_")
    target = backup_dir / f"{safe}_{PATCH_NAME}_{stamp}.bak"
    shutil.copy2(path, target)
    return target


def assigned_names(node):
    result = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            result.add(child.id)
    return result


def final_function_positions(tree):
    positions = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            positions[node.name] = node.lineno
    return positions


def validate_equipment_module(path):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    final_positions = final_function_positions(tree)
    missing = sorted(REQUIRED_DIRECT_FUNCTIONS - set(final_positions))
    if missing:
        raise RuntimeError("У equipment_system.py відсутні фінальні функції: " + ", ".join(missing))

    # Direct implementation markers must appear before the final functions.
    required_markers = (
        "9.0.12f1",
        "9.0.12f2",
        "9.0.12f3",
        "9.0.12h1",
        "9.0.12h2",
        "9.0.12h3",
    )
    absent_markers = [m for m in required_markers if m not in text]
    if absent_markers:
        raise RuntimeError("Не знайдено маркери прямих реалізацій: " + ", ".join(absent_markers))
    return final_positions


def remove_safe_capture_blocks(db_path):
    text = db_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    ranges = []
    removed_names = set()

    for node in tree.body:
        names = assigned_names(node)
        matched = names & SAFE_LEGACY_NAMES
        if not matched:
            continue
        # Only remove self-contained top-level try/assign capture statements.
        if not isinstance(node, (ast.Try, ast.Assign, ast.AnnAssign)):
            continue
        if names - SAFE_LEGACY_NAMES:
            continue
        start = node.lineno - 1
        end = getattr(node, "end_lineno", node.lineno)
        ranges.append((start, end))
        removed_names.update(matched)

    if not ranges:
        return text, []

    for start, end in sorted(ranges, reverse=True):
        del lines[start:end]

    new_text = "".join(lines)
    ast.parse(new_text)
    return new_text, sorted(removed_names)


def run_check(root, args):
    proc = subprocess.run(
        [sys.executable, *args],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Команда завершилася з помилкою: {' '.join(args)}\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout.strip()


def main():
    root = Path(__file__).resolve().parents[1]
    db_path = root / "db.py"
    equipment_path = root / "systems" / "equipment_system.py"
    report_path = root / "DB_CLEANUP_9_0_12_REPORT.md"
    audit_path = root / "DB_CLEANUP_9_0_12I1_AUDIT.md"

    for path in (db_path, equipment_path):
        if not path.exists():
            raise SystemExit(f"❌ Не знайдено файл: {path}")

    validate_equipment_module(equipment_path)

    original_db = db_path.read_text(encoding="utf-8")
    backup = backup_file(root, db_path)

    before_report = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    new_db, removed = remove_safe_capture_blocks(db_path)

    if not removed:
        print("ℹ️ Безпечні equipment legacy captures уже видалені або не знайдені.")
        print("✅ Змін у db.py не внесено.")
        return

    expected_missing = sorted(SAFE_LEGACY_NAMES - set(removed))
    if expected_missing:
        db_path.write_text(original_db, encoding="utf-8")
        raise SystemExit(
            "❌ Патч зупинено: знайдено не всі очікувані capture-блоки.\n"
            "Не знайдено: " + ", ".join(expected_missing)
        )

    db_path.write_text(new_db, encoding="utf-8")

    try:
        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(equipment_path), doraise=True)

        checks = [
            ["tools/check_imports.py"],
            ["tools/smoke_test_rom_core.py"],
            ["tools/smoke_test_equipment_readonly_core.py"],
            ["tools/smoke_test_inventory_refine_contracts.py"],
            ["tools/smoke_test_weapon_damage_contracts.py"],
            ["tools/smoke_test_player_combat_stats.py"],
            ["tools/smoke_test_equipment_write_contracts.py"],
            ["tools/smoke_test_equipment_durability_contracts.py"],
            ["tools/smoke_test_equipment_trader_contracts.py"],
            ["tools/db_cleanup_readiness.py"],
        ]
        outputs = []
        for args in checks:
            outputs.append((" ".join(args), run_check(root, args)))

        after_report = report_path.read_text(encoding="utf-8") if report_path.exists() else ""

        audit_lines = [
            "# DB Cleanup 9.0.12i1 Audit",
            "",
            f"Дата: {datetime.now().isoformat(timespec='seconds')}",
            "",
            "## Видалені безпечні legacy captures",
            "",
        ]
        audit_lines.extend(f"- `{name}`" for name in removed)
        audit_lines.extend([
            "",
            "## Що навмисно залишено",
            "",
            "- `_legacy_equipment_ro_v1_can_equip_item_by_class`",
            "- `_legacy_equipment_ro_v1_can_equip_inventory_item_by_class`",
            "- `_legacy_equipment_ro_v1_is_inventory_item_class_compatible`",
            "",
            "Ці три class-compatibility captures залишені до окремого перенесення правил сумісності.",
            "",
            "## Readiness до патча",
            "",
            "```text",
            before_report[:12000],
            "```",
            "",
            "## Readiness після патча",
            "",
            "```text",
            after_report[:12000],
            "```",
            "",
            "## Результати перевірок",
            "",
        ])
        for command, output in outputs:
            audit_lines.extend([f"### `{command}`", "", "```text", output, "```", ""])
        audit_path.write_text("\n".join(audit_lines), encoding="utf-8")

    except Exception as exc:
        db_path.write_text(original_db, encoding="utf-8")
        py_compile.compile(str(db_path), doraise=True)
        raise SystemExit(
            "❌ Патч 9.0.12i1 завершився помилкою. db.py автоматично відновлено.\n\n"
            f"Помилка:\n{exc}"
        )

    print("✅ Патч 9.0.12i1 успішно застосовано.")
    print(f"✅ Видалено безпечних equipment legacy captures: {len(removed)}")
    print("✅ Великі історичні реалізації та class-compatibility captures не видалялися.")
    print("✅ Усі автоматичні перевірки пройшли успішно.")
    print("Резервна копія:")
    print(f"- {backup}")
    print("Звіт:")
    print(f"- {audit_path}")
    print("Видалені captures:")
    for name in removed:
        print(f"- {name}")


if __name__ == "__main__":
    main()
