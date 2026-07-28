#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i6b: physically remove confirmed Equipment read-only duplicates from db.py."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.12i6b"
TARGETS = (
    "ensure_equipment_slots",
    "get_all_equipped_items",
    "get_inventory_detailed",
    "get_inventory_entry",
    "get_item_by_inventory_id",
    "get_item_by_inventory_id_full",
    "get_item_bonuses",
    "get_equipped_item_defenses",
    "get_sellable_equipment_items",
    "get_inventory_refine_level",
    "get_inventory_refined_display_name",
    "format_refined_item_name",
    "init_weapon_damage_system",
    "calculate_weapon_damage_by_values",
    "get_weapon_damage_by_inventory_id",
    "get_inventory_weapon_damage_display",
)
AUDIT_NAME = "audit_equipment_readonly_duplicates.py"
REQUIRED_TESTS = (
    "smoke_test_equipment_readonly_core.py",
    "smoke_test_inventory_refine_contracts.py",
    "smoke_test_weapon_damage_contracts.py",
)

POST_AUDIT = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i6b: verify Equipment read-only physical cleanup."""
from __future__ import annotations
import ast
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGETS = (
    "ensure_equipment_slots", "get_all_equipped_items", "get_inventory_detailed",
    "get_inventory_entry", "get_item_by_inventory_id", "get_item_by_inventory_id_full",
    "get_item_bonuses", "get_equipped_item_defenses", "get_sellable_equipment_items",
    "get_inventory_refine_level", "get_inventory_refined_display_name",
    "format_refined_item_name", "init_weapon_damage_system",
    "calculate_weapon_damage_by_values", "get_weapon_damage_by_inventory_id",
    "get_inventory_weapon_damage_display",
)
REPORT = ROOT / "DB_CLEANUP_9_0_12I6B_EQUIPMENT_READONLY_PHYSICAL_CLEANUP.md"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def parse(path):
    text = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(text, filename=str(path))
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.setdefault(node.name, []).append(node)
    return text, result


def safe(function, *args):
    try:
        return True, function(*args)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def main():
    db_text, db_defs = parse(ROOT / "db.py")
    system_text, system_defs = parse(ROOT / "systems" / "equipment_system.py")

    import db
    from systems import equipment_system as equipment

    for name in TARGETS:
        if len(db_defs.get(name, [])) != 1:
            fail(f"db.py {name}: definitions={len(db_defs.get(name, []))}, expected 1")
        if len(system_defs.get(name, [])) < 1:
            fail(f"equipment_system.py missing {name}")
        wrapper = ast.get_source_segment(db_text, db_defs[name][0]) or ""
        system = ast.get_source_segment(system_text, system_defs[name][-1]) or ""
        if "equipment_system" not in wrapper:
            fail(f"db.{name} is not an Equipment System wrapper")
        if "_call_legacy" in system:
            fail(f"final equipment_system.{name} still calls _call_legacy")

    users = [int(row[0]) for row in db.cursor.execute("SELECT user_id FROM users ORDER BY user_id").fetchall()]
    comparisons = 0
    for user_id in users:
        for name in (
            "get_all_equipped_items", "get_inventory_detailed", "get_item_bonuses",
            "get_equipped_item_defenses", "get_sellable_equipment_items",
        ):
            if safe(getattr(db, name), user_id) != safe(getattr(equipment, name), user_id):
                fail(f"user comparison mismatch: {name}, user={user_id}")
            comparisons += 1

        inventory_rows = db.cursor.execute(
            "SELECT id FROM inventory WHERE user_id=? ORDER BY id LIMIT 20", (user_id,)
        ).fetchall()
        for (inventory_id,) in inventory_rows:
            for name in (
                "get_inventory_entry", "get_item_by_inventory_id",
                "get_item_by_inventory_id_full", "get_inventory_refine_level",
                "get_inventory_refined_display_name", "get_weapon_damage_by_inventory_id",
                "get_inventory_weapon_damage_display",
            ):
                if safe(getattr(db, name), inventory_id) != safe(getattr(equipment, name), inventory_id):
                    fail(f"item comparison mismatch: {name}, inventory={inventory_id}")
                comparisons += 1

    pure_cases = (
        ("calculate_weapon_damage_by_values", (8, 12, 1, "common")),
        ("format_refined_item_name", ("Item", 3)),
    )
    for name, args in pure_cases:
        if safe(getattr(db, name), *args) != safe(getattr(equipment, name), *args):
            fail(f"pure API mismatch: {name}")

    report = [
        "# ROM 9.0.12i6b - Equipment Read-only Physical Cleanup",
        "",
        "## Result",
        "",
        f"- Public Equipment wrappers remaining in `db.py`: {len(TARGETS)}",
        "- Earlier definitions for these APIs remaining: 0",
        f"- Public/system read-only comparisons: {comparisons}",
        f"- Pure API comparisons: {len(pure_cases)}",
        "- Mismatches: 0",
        "- Final system `_call_legacy` dependencies: 0",
        "- Database mutations performed by this audit: 0",
        "",
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] equipment read-only physical cleanup audit")
    print(f"- public wrappers: {len(TARGETS)}")
    print("- earlier Equipment read-only definitions: 0")
    print(f"- public/system comparisons: {comparisons}")
    print(f"- pure API comparisons: {len(pure_cases)}")
    print("- mismatches: 0")
    print("- final system legacy delegation: 0")
    print("- database mutations: 0")
    print(f"- report: {REPORT}")


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
        if (root / "db.py").is_file() and (root / "systems" / "equipment_system.py").is_file():
            return root
    fail("Не знайдено корінь ROM.")


def function_map(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.setdefault(node.name, []).append(node)
    return result


def node_start(node):
    decorators = getattr(node, "decorator_list", None) or []
    return min([node.lineno] + [decorator.lineno for decorator in decorators])


def run_checked(root, path, label):
    result = subprocess.run([sys.executable, str(path)], cwd=root, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{label} exit code {result.returncode}")


def main():
    root = find_root()
    db_path = root / "db.py"
    system_path = root / "systems" / "equipment_system.py"
    tools = root / "tools"
    audit_path = tools / AUDIT_NAME
    readiness_path = tools / "db_cleanup_readiness.py"

    for test_name in REQUIRED_TESTS:
        if not (tools / test_name).is_file():
            fail(f"Відсутній tools/{test_name}.")

    source = db_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(db_path))
    functions = function_map(tree)

    already_clean = all(len(functions.get(name, [])) == 1 for name in TARGETS)
    if already_clean:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
        if audit_path.is_file():
            run_checked(root, audit_path, "post-cleanup audit")
        for test_name in REQUIRED_TESTS:
            run_checked(root, tools / test_name, test_name)
        return

    system_source = system_path.read_text(encoding="utf-8-sig")
    system_tree = ast.parse(system_source, filename=str(system_path))
    system_functions = function_map(system_tree)

    remove = []
    removed_by_name = {}
    for name in TARGETS:
        nodes = functions.get(name, [])
        if len(nodes) < 2:
            fail(f"db.py {name}: definitions={len(nodes)}, очікувалося щонайменше 2.")
        final_wrapper = ast.get_source_segment(source, nodes[-1]) or ""
        if "equipment_system" not in final_wrapper:
            fail(f"Фінальна db.{name} не є wrapper у equipment_system.")
        system_nodes = system_functions.get(name, [])
        if not system_nodes:
            fail(f"systems/equipment_system.py не містить {name}.")
        system_final = ast.get_source_segment(system_source, system_nodes[-1]) or ""
        if "_call_legacy" in system_final:
            fail(f"Фінальна equipment_system.{name} все ще залежить від _call_legacy.")
        removed_by_name[name] = len(nodes) - 1
        for node in nodes[:-1]:
            remove.append((node_start(node), node.end_lineno, name))

    ordered = sorted(remove)
    for previous, current in zip(ordered, ordered[1:]):
        if current[0] <= previous[1]:
            fail(f"Діапазони видалення перетинаються: {previous[2]} / {current[2]}")

    lines = source.splitlines(keepends=True)
    for start, end, _name in sorted(remove, reverse=True):
        del lines[start - 1:end]
    updated = "".join(lines)

    updated_tree = ast.parse(updated, filename=str(db_path))
    updated_functions = function_map(updated_tree)
    for name in TARGETS:
        if len(updated_functions.get(name, [])) != 1:
            fail(f"Після очищення db.{name}: definitions={len(updated_functions.get(name, []))}")
        wrapper = ast.get_source_segment(updated, updated_functions[name][0]) or ""
        if "equipment_system" not in wrapper:
            fail(f"Після очищення db.{name} не є wrapper.")

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_backup = backup_dir / f"db.py_{PATCH_ID}_equipment_readonly_cleanup_{stamp}.bak"
    shutil.copy2(db_path, db_backup)
    audit_backup = None
    if audit_path.exists():
        audit_backup = backup_dir / f"tools_{AUDIT_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(audit_path, audit_backup)

    temp = db_path.with_name(".db.i6b.tmp")
    try:
        temp.write_text(updated, encoding="utf-8")
        os.replace(temp, db_path)
        audit_path.write_text(POST_AUDIT, encoding="utf-8")
        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(system_path), doraise=True)
        py_compile.compile(str(audit_path), doraise=True)

        run_checked(root, audit_path, "post-cleanup audit")
        for test_name in REQUIRED_TESTS:
            run_checked(root, tools / test_name, test_name)

        readiness = subprocess.run(
            [sys.executable, str(readiness_path)], cwd=root,
            text=True, capture_output=True, check=False
        )
        print(readiness.stdout, end="")
        if readiness.returncode != 0:
            raise RuntimeError(f"readiness exit code {readiness.returncode}")
        if "legacy_refs: 0" not in readiness.stdout or "unsafe_delete: 0" not in readiness.stdout:
            raise RuntimeError("readiness safety metrics changed unexpectedly")
    except Exception as exc:
        shutil.copy2(db_backup, db_path)
        if audit_backup is not None:
            shutil.copy2(audit_backup, audit_path)
        elif audit_path.exists():
            audit_path.unlink()
        if temp.exists():
            temp.unlink()
        fail(f"Перевірка не пройдена; файли відновлено: {exc}")

    removed_total = sum(removed_by_name.values())
    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print(f"✅ Фізично видалено ранніх Equipment read-only визначень: {removed_total}")
    print(f"✅ Залишено публічних Equipment wrappers: {len(TARGETS)}")
    print("✅ Read-only, inventory/refine та weapon-damage тести пройдені.")
    print("Резервні копії:")
    print(f"   {db_backup.relative_to(root)}")
    if audit_backup is not None:
        print(f"   {audit_backup.relative_to(root)}")
    print("Перевірки:")
    print("   python -m py_compile ./db.py")
    print("   python -m py_compile ./systems/equipment_system.py")
    print("   python ./tools/audit_equipment_readonly_duplicates.py")
    print("   python ./tools/smoke_test_equipment_readonly_core.py")
    print("   python ./tools/smoke_test_inventory_refine_contracts.py")
    print("   python ./tools/smoke_test_weapon_damage_contracts.py")
    print("   python ./tools/smoke_test_equipment_trader_contracts.py")
    print("   python ./tools/smoke_test_player_combat_stats.py")
    print("   python ./tools/smoke_test_rom_core.py")
    print("   python ./tools/check_imports.py")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
