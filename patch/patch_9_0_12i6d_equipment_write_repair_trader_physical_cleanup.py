#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i6d: remove confirmed Equipment write/repair/trader duplicates."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.12i6d"
TARGETS = (
    "equip_inventory_item",
    "unequip_inventory_item",
    "unequip_incompatible_items_after_class_change",
    "calculate_repair_cost",
    "repair_equipped_item",
    "repair_all_equipped",
    "damage_equipped_items_on_death",
    "sell_inventory_item_to_trader",
    "buy_item_for_gold",
    "buy_common_equipment_from_trader",
)
AUDIT_NAME = "audit_equipment_write_repair_trader.py"
AUTOMATIC_TESTS = (
    "smoke_test_equipment_write_contracts.py",
    "smoke_test_equipment_class_compatibility.py",
    "smoke_test_equipment_durability_contracts.py",
    "smoke_test_equipment_trader_contracts.py",
    "smoke_test_equipment_readonly_core.py",
    "smoke_test_inventory_refine_contracts.py",
    "smoke_test_weapon_damage_contracts.py",
    "smoke_test_player_combat_stats.py",
    "smoke_test_rom_core.py",
    "check_imports.py",
)

POST_AUDIT = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i6d: post-cleanup Equipment write/repair/trader audit."""
from __future__ import annotations
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGETS = (
    "equip_inventory_item", "unequip_inventory_item",
    "unequip_incompatible_items_after_class_change", "calculate_repair_cost",
    "repair_equipped_item", "repair_all_equipped",
    "damage_equipped_items_on_death", "sell_inventory_item_to_trader",
    "buy_item_for_gold", "buy_common_equipment_from_trader",
)
REPORT = ROOT / "DB_CLEANUP_9_0_12I6D_EQUIPMENT_WRITE_REPAIR_TRADER_PHYSICAL_CLEANUP.md"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def parse(path):
    text = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(text, filename=str(path))
    definitions = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.setdefault(node.name, []).append(node)
    return text, definitions


def safe(function, *args, **kwargs):
    try:
        return True, function(*args, **kwargs)
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
        if not system_defs.get(name):
            fail(f"equipment_system.py missing {name}")
        wrapper = ast.get_source_segment(db_text, db_defs[name][0]) or ""
        system_final = ast.get_source_segment(system_text, system_defs[name][-1]) or ""
        if "equipment_system" not in wrapper:
            fail(f"db.{name} is not an Equipment System wrapper")
        if "_call_legacy" in system_final:
            fail(f"final equipment_system.{name} still calls _call_legacy")

    repair_cases = 0
    for durability in (-10, 0, 1, 50, 99, 100, 120, None):
        for rarity in ("common", "uncommon", "rare", "epic", None):
            public = safe(db.calculate_repair_cost, durability, rarity)
            direct = safe(equipment.calculate_repair_cost, durability, rarity)
            if public != direct:
                fail(f"repair-cost mismatch: durability={durability}, rarity={rarity}")
            repair_cases += 1

    missing_uid = -987654321
    missing_iid = -987654322
    before_users = db.cursor.execute(
        "SELECT COUNT(*) FROM users WHERE user_id=?", (missing_uid,)
    ).fetchone()[0]
    before_inventory = db.cursor.execute(
        "SELECT COUNT(*) FROM inventory WHERE id=? OR user_id=?",
        (missing_iid, missing_uid),
    ).fetchone()[0]

    protected_cases = (
        ("equip_inventory_item", (missing_uid, missing_iid), {}),
        ("unequip_inventory_item", (missing_uid, missing_iid), {}),
        ("unequip_incompatible_items_after_class_change", (missing_uid,), {}),
        ("repair_equipped_item", (missing_uid, missing_iid), {}),
        ("repair_all_equipped", (missing_uid,), {}),
        ("damage_equipped_items_on_death", (missing_uid,), {}),
        ("sell_inventory_item_to_trader", (missing_uid, missing_iid), {}),
        ("buy_item_for_gold", (missing_uid, missing_iid, 10.0), {}),
        ("buy_common_equipment_from_trader", (missing_uid, "__invalid_slot__"), {}),
    )
    protected = 0
    for name, args, kwargs in protected_cases:
        public = safe(getattr(db, name), *args, **kwargs)
        direct = safe(getattr(equipment, name), *args, **kwargs)
        if public != direct:
            fail(f"protected-path mismatch {name}: public={public!r}, direct={direct!r}")
        protected += 1

    after_users = db.cursor.execute(
        "SELECT COUNT(*) FROM users WHERE user_id=?", (missing_uid,)
    ).fetchone()[0]
    after_inventory = db.cursor.execute(
        "SELECT COUNT(*) FROM inventory WHERE id=? OR user_id=?",
        (missing_iid, missing_uid),
    ).fetchone()[0]
    if (before_users, before_inventory) != (after_users, after_inventory):
        fail("protected paths changed database rows")

    report = [
        "# ROM 9.0.12i6d - Equipment Write Repair Trader Physical Cleanup",
        "",
        "## Result",
        "",
        f"- Public wrappers remaining in `db.py`: {len(TARGETS)}",
        "- Earlier definitions for these APIs remaining: 0",
        f"- Repair-cost equivalence cases: {repair_cases}",
        f"- Protected missing-ID comparisons: {protected}",
        "- Mismatches: 0",
        "- Final system `_call_legacy` dependencies: 0",
        "- Real-user mutations performed by this audit: 0",
        "",
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] equipment write/repair/trader physical cleanup audit")
    print(f"- public wrappers: {len(TARGETS)}")
    print("- earlier write/repair/trader definitions: 0")
    print(f"- repair-cost equivalence cases: {repair_cases}")
    print(f"- protected missing-ID comparisons: {protected}")
    print("- mismatches: 0")
    print("- final system legacy delegation: 0")
    print("- real user mutations: 0")
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
    definitions = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.setdefault(node.name, []).append(node)
    return definitions


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

    for test_name in AUTOMATIC_TESTS:
        if not (tools / test_name).is_file():
            fail(f"Відсутній tools/{test_name}.")

    source = db_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(db_path))
    definitions = function_map(tree)

    already_clean = all(len(definitions.get(name, [])) == 1 for name in TARGETS)
    if already_clean:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
        if audit_path.is_file():
            run_checked(root, audit_path, "post-cleanup audit")
        for test_name in AUTOMATIC_TESTS:
            run_checked(root, tools / test_name, test_name)
        return

    system_source = system_path.read_text(encoding="utf-8-sig")
    system_tree = ast.parse(system_source, filename=str(system_path))
    system_definitions = function_map(system_tree)

    remove = []
    removed_by_name = {}
    for name in TARGETS:
        nodes = definitions.get(name, [])
        if len(nodes) < 2:
            fail(f"db.py {name}: definitions={len(nodes)}, очікувалося щонайменше 2.")
        final_wrapper = ast.get_source_segment(source, nodes[-1]) or ""
        if "equipment_system" not in final_wrapper:
            fail(f"Фінальна db.{name} не є wrapper у equipment_system.")
        system_nodes = system_definitions.get(name, [])
        if not system_nodes:
            fail(f"systems/equipment_system.py не містить {name}.")
        system_final = ast.get_source_segment(system_source, system_nodes[-1]) or ""
        if "_call_legacy" in system_final:
            fail(f"Фінальна equipment_system.{name} залежить від _call_legacy.")
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
    updated_definitions = function_map(updated_tree)
    for name in TARGETS:
        if len(updated_definitions.get(name, [])) != 1:
            fail(f"Після очищення db.{name}: definitions={len(updated_definitions.get(name, []))}")
        wrapper = ast.get_source_segment(updated, updated_definitions[name][0]) or ""
        if "equipment_system" not in wrapper:
            fail(f"Після очищення db.{name} не є wrapper.")

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_backup = backup_dir / f"db.py_{PATCH_ID}_write_repair_trader_cleanup_{stamp}.bak"
    shutil.copy2(db_path, db_backup)
    audit_backup = None
    if audit_path.exists():
        audit_backup = backup_dir / f"tools_{AUDIT_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(audit_path, audit_backup)

    temp = db_path.with_name(".db.i6d.tmp")
    try:
        temp.write_text(updated, encoding="utf-8")
        os.replace(temp, db_path)
        audit_path.write_text(POST_AUDIT, encoding="utf-8")

        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(system_path), doraise=True)
        py_compile.compile(str(audit_path), doraise=True)

        run_checked(root, audit_path, "post-cleanup audit")
        for test_name in AUTOMATIC_TESTS:
            run_checked(root, tools / test_name, test_name)

        readiness = subprocess.run(
            [sys.executable, str(readiness_path)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        print(readiness.stdout, end="")
        if readiness.returncode != 0:
            raise RuntimeError(f"readiness exit code {readiness.returncode}")
        if "legacy_refs: 0" not in readiness.stdout:
            raise RuntimeError("readiness не підтвердив legacy_refs: 0")
        if "unsafe_delete: 0" not in readiness.stdout:
            raise RuntimeError("readiness не підтвердив unsafe_delete: 0")
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
    print(f"✅ Фізично видалено ранніх Equipment write/repair/trader визначень: {removed_total}")
    print(f"✅ Залишено публічних Equipment wrappers: {len(TARGETS)}")
    print("✅ Усі Equipment та core contract-тести пройдені.")
    print("Резервні копії:")
    print(f"   {db_backup.relative_to(root)}")
    if audit_backup is not None:
        print(f"   {audit_backup.relative_to(root)}")
    print("Перевірки:")
    print("   python -m py_compile ./db.py")
    print("   python -m py_compile ./systems/equipment_system.py")
    print("   python ./tools/audit_equipment_write_repair_trader.py")
    for test_name in AUTOMATIC_TESTS:
        print(f"   python ./tools/{test_name}")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
