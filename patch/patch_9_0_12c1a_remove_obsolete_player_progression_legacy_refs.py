from pathlib import Path
from datetime import datetime
import ast
import py_compile
import re

PATCH_NAME = "9_0_12c1a_remove_obsolete_player_progression_legacy_refs"

TARGET_FUNCTIONS = {
    "get_player_level",
    "get_wallet",
    "add_gold",
    "add_kill",
    "get_current_hp_raw",
    "get_current_hp",
    "set_current_hp",
}


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup


def assigned_name(node):
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def is_target_legacy_name(name):
    low = name.lower()
    if "legacy" not in low:
        return False
    return any(func in name for func in TARGET_FUNCTIONS)


def remove_unused_simple_legacy_assignments(text, path_label):
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    removals = []
    kept = []

    for node in tree.body:
        name = assigned_name(node)
        if not name or not is_target_legacy_name(name):
            continue

        # Conservative rule: remove only when the variable occurs once in the file,
        # meaning only its assignment remains and no runtime code reads it.
        occurrences = len(re.findall(rf"\b{re.escape(name)}\b", text))
        if occurrences == 1:
            start = node.lineno - 1
            end = getattr(node, "end_lineno", node.lineno)
            removals.append((start, end, name))
        else:
            kept.append((name, occurrences))

    for start, end, _name in sorted(removals, reverse=True):
        del lines[start:end]

    cleaned = "".join(lines)
    return cleaned, removals, kept


def verify_direct_runtime_contracts(root):
    # Import only after patched files compile. Add root to sys.path.
    import sys
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    import db

    # Structural checks only; no balance-changing writes.
    required = [
        "get_player_level",
        "get_wallet",
        "add_gold",
        "add_kill",
        "get_current_hp_raw",
        "get_current_hp",
        "set_current_hp",
    ]
    missing = [name for name in required if not callable(getattr(db, name, None))]
    if missing:
        raise RuntimeError(f"Missing player progression API after cleanup: {missing}")


def main():
    root = Path(__file__).resolve().parents[1]
    targets = [root / "db.py", root / "systems" / "player_system.py"]

    for target in targets:
        if not target.exists():
            raise SystemExit(f"❌ Не знайдено файл: {target}")

    originals = {p: p.read_text(encoding="utf-8") for p in targets}
    backups = {p: make_backup(root, p) for p in targets}
    all_removed = []
    all_kept = []

    try:
        for target in targets:
            cleaned, removed, kept = remove_unused_simple_legacy_assignments(
                originals[target], str(target.relative_to(root))
            )
            target.write_text(cleaned, encoding="utf-8")
            all_removed.extend((str(target.relative_to(root)), name) for _, _, name in removed)
            all_kept.extend((str(target.relative_to(root)), name, count) for name, count in kept)

        for target in targets:
            py_compile.compile(str(target), doraise=True)

        verify_direct_runtime_contracts(root)

    except Exception as error:
        for target, original in originals.items():
            target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка під час cleanup. Файли автоматично відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.12c1a застосовано успішно.")
    print("✅ Видалено тільки невикористовувані simple legacy assignments.")
    print("✅ Ігрові функції та старі function definitions не видалялися.")
    print()
    print("Backup:")
    for target in targets:
        print(f"- {backups[target]}")
    print()
    print(f"Removed legacy refs: {len(all_removed)}")
    for file_name, name in all_removed:
        print(f"- {file_name}: {name}")

    if all_kept:
        print()
        print("Залишено через наявні runtime-посилання:")
        for file_name, name, count in all_kept:
            print(f"- {file_name}: {name} (occurrences={count})")

    print()
    if not all_removed:
        print("ℹ️ Безпечних невикористовуваних refs не знайдено.")
        print("Це не помилка: патч навмисно не видаляє змінні, які ще десь читаються.")
    print()
    print("Після патча запусти:")
    print("python -m py_compile .\\systems\\player_system.py")
    print("python -m py_compile .\\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")
    print("python tools/smoke_test_player_contracts.py")
    print("python tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
