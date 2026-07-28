#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i5c: physically remove confirmed Character duplicates from db.py."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.12i5c"
TARGETS = (
    "normalize_character_name",
    "validate_character_name",
    "get_character_name",
    "set_character_name",
    "get_character_class",
    "set_character_class",
    "get_character_class_display",
    "get_character_resource_type",
    "get_max_mp",
    "get_user_mp",
    "set_user_mp",
    "refresh_user_mp",
    "grant_class_change_available",
    "consume_class_change_available",
    "has_class_change_available",
)
PRESERVE = (
    "get_class_change_available",
    "is_character_name_taken",
    "needs_character_name",
    "needs_character_class",
)
MUTATION_TEST = "smoke_test_character_mutation_contracts.py"
AUDIT_TEST = "audit_character_duplicates.py"

POST_AUDIT = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i5c: verify Character physical cleanup."""
from __future__ import annotations
import ast
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGETS = (
    "normalize_character_name", "validate_character_name", "get_character_name",
    "set_character_name", "get_character_class", "set_character_class",
    "get_character_class_display", "get_character_resource_type", "get_max_mp",
    "get_user_mp", "set_user_mp", "refresh_user_mp",
    "grant_class_change_available", "consume_class_change_available",
    "has_class_change_available",
)
PRESERVE = (
    "get_class_change_available", "is_character_name_taken",
    "needs_character_name", "needs_character_class",
)
REPORT = ROOT / "DB_CLEANUP_9_0_12I5C_CHARACTER_PHYSICAL_CLEANUP.md"


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
    system_text, system_defs = parse(ROOT / "systems" / "character_system.py")

    import db
    from systems import character_system as character

    for name in TARGETS:
        if len(db_defs.get(name, [])) != 1:
            fail(f"db.py {name}: definitions={len(db_defs.get(name, []))}, expected 1")
        if len(system_defs.get(name, [])) < 1:
            fail(f"character_system.py missing {name}")
        wrapper = ast.get_source_segment(db_text, db_defs[name][0]) or ""
        if "character_system" not in wrapper:
            fail(f"db.{name} is not a Character System wrapper")

    for name in PRESERVE:
        if len(db_defs.get(name, [])) != 1:
            fail(f"preserved db helper {name}: definitions={len(db_defs.get(name, []))}")

    if str(inspect.signature(db.set_user_mp)) != "(user_id, mp)":
        fail("public set_user_mp signature changed")
    if str(inspect.signature(character.set_user_mp)) != "(user_id, amount)":
        fail("system set_user_mp signature changed")

    getters = (
        "get_character_name", "get_character_class", "get_character_class_display",
        "get_character_resource_type", "get_max_mp", "get_user_mp",
        "get_class_change_available", "has_class_change_available",
    )
    users = [int(row[0]) for row in db.cursor.execute("SELECT user_id FROM users ORDER BY user_id").fetchall()]
    comparisons = 0
    for user_id in users:
        for name in getters:
            if safe(getattr(db, name), user_id) != safe(getattr(character, name), user_id):
                fail(f"getter mismatch: {name}, user={user_id}")
            comparisons += 1

    samples = ("", "  x  ", "11", "A B")
    pure = 0
    for value in samples:
        for name in ("normalize_character_name", "validate_character_name"):
            if safe(getattr(db, name), value) != safe(getattr(character, name), value):
                fail(f"pure-function mismatch: {name}")
            pure += 1

    report = [
        "# ROM 9.0.12i5c - Character Physical Cleanup",
        "",
        "## Result",
        "",
        f"- Character public wrappers remaining in `db.py`: {len(TARGETS)}",
        "- Earlier Character definitions remaining: 0",
        f"- Read-only getter comparisons: {comparisons}",
        f"- Pure-function comparisons: {pure}",
        "- Mismatches: 0",
        "- Public `set_user_mp(user_id, mp)` signature preserved: yes",
        "- Unique Character helpers preserved: yes",
        "- Database mutations performed by this audit: 0",
        "",
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] character physical cleanup audit")
    print(f"- public wrappers: {len(TARGETS)}")
    print("- earlier Character definitions: 0")
    print(f"- getter comparisons: {comparisons}")
    print(f"- pure-function comparisons: {pure}")
    print("- mismatches: 0")
    print("- preserved unique helpers: OK")
    print("- database mutations: 0")
    print(f"- report: {REPORT}")


if __name__ == "__main__":
    main()
'''


def fail(message: str) -> None:
    print(f"❌ {message}")
    raise SystemExit(1)


def find_root() -> Path:
    here = Path(__file__).resolve()
    for root in (here.parent.parent, Path.cwd(), Path.cwd().parent):
        root = root.resolve()
        if (root / "db.py").is_file() and (root / "systems" / "character_system.py").is_file():
            return root
    fail("Не знайдено корінь ROM.")
    raise AssertionError("unreachable")


def function_map(tree: ast.Module):
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.setdefault(node.name, []).append(node)
    return result


def node_start(node):
    decorators = getattr(node, "decorator_list", None) or []
    return min([node.lineno] + [decorator.lineno for decorator in decorators])


def run_checked(root: Path, path: Path, label: str) -> None:
    result = subprocess.run([sys.executable, str(path)], cwd=root, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{label} exit code {result.returncode}")


def main() -> None:
    root = find_root()
    db_path = root / "db.py"
    system_path = root / "systems" / "character_system.py"
    tools_dir = root / "tools"
    mutation_path = tools_dir / MUTATION_TEST
    audit_path = tools_dir / AUDIT_TEST
    readiness_path = tools_dir / "db_cleanup_readiness.py"

    source = db_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(db_path))
    functions = function_map(tree)

    already_clean = all(len(functions.get(name, [])) == 1 for name in TARGETS)
    if already_clean:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
        if audit_path.is_file():
            run_checked(root, audit_path, "post-cleanup audit")
        if mutation_path.is_file():
            run_checked(root, mutation_path, "mutation contracts")
        return

    if not mutation_path.is_file():
        fail(f"Відсутній tools/{MUTATION_TEST}; спочатку застосуй i5b.")

    system_source = system_path.read_text(encoding="utf-8-sig")
    system_tree = ast.parse(system_source, filename=str(system_path))
    system_functions = function_map(system_tree)

    remove = []
    removed_by_name = {}
    for name in TARGETS:
        nodes = functions.get(name, [])
        if len(nodes) < 2:
            fail(f"db.py {name}: definitions={len(nodes)}, очікувалося щонайменше 2.")
        final_source = ast.get_source_segment(source, nodes[-1]) or ""
        if "character_system" not in final_source:
            fail(f"Фінальна db.{name} не є wrapper у character_system.")
        if not system_functions.get(name):
            fail(f"systems/character_system.py не містить {name}.")
        removed_by_name[name] = len(nodes) - 1
        for node in nodes[:-1]:
            remove.append((node_start(node), node.end_lineno, name))

    preserve_before = {name: len(functions.get(name, [])) for name in PRESERVE}
    if any(count != 1 for count in preserve_before.values()):
        fail(f"Неочікуваний стан унікальних helpers: {preserve_before}")

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
        final_source = ast.get_source_segment(updated, updated_functions[name][0]) or ""
        if "character_system" not in final_source:
            fail(f"Після очищення db.{name} не є wrapper.")
    preserve_after = {name: len(updated_functions.get(name, [])) for name in PRESERVE}
    if preserve_after != preserve_before:
        fail("Патч зачепив унікальні Character helpers.")

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_backup = backup_dir / f"db.py_{PATCH_ID}_character_physical_cleanup_{stamp}.bak"
    shutil.copy2(db_path, db_backup)
    audit_backup = None
    if audit_path.exists():
        audit_backup = backup_dir / f"tools_{AUDIT_TEST}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(audit_path, audit_backup)

    temp = db_path.with_name(".db.i5c.tmp")
    try:
        temp.write_text(updated, encoding="utf-8")
        os.replace(temp, db_path)
        audit_path.write_text(POST_AUDIT, encoding="utf-8")
        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(system_path), doraise=True)
        py_compile.compile(str(audit_path), doraise=True)
        run_checked(root, audit_path, "post-cleanup audit")
        run_checked(root, mutation_path, "mutation contracts")

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
    print(f"✅ Фізично видалено ранніх Character-визначень: {removed_total}")
    print(f"✅ Залишено публічних Character wrappers: {len(TARGETS)}")
    print("✅ Унікальні Character helpers збережено.")
    print("✅ Mutation contracts і post-cleanup audit пройдені.")
    print("Резервні копії:")
    print(f"   {db_backup.relative_to(root)}")
    if audit_backup is not None:
        print(f"   {audit_backup.relative_to(root)}")
    print("Перевірки:")
    print("   python -m py_compile ./db.py")
    print("   python -m py_compile ./systems/character_system.py")
    print("   python ./tools/audit_character_duplicates.py")
    print("   python ./tools/smoke_test_character_mutation_contracts.py")
    print("   python ./tools/smoke_test_player_contracts.py")
    print("   python ./tools/smoke_test_player_combat_stats.py")
    print("   python ./tools/smoke_test_equipment_write_contracts.py")
    print("   python ./tools/smoke_test_rom_core.py")
    print("   python ./tools/check_imports.py")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
