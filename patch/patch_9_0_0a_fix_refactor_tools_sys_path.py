from pathlib import Path
from datetime import datetime
import py_compile


PATCH_NAME = "9_0_0a_fix_refactor_tools_sys_path"


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"

    backup_path.write_text(
        target.read_text(encoding="utf-8"),
        encoding="utf-8"
    )

    return backup_path


def write_check_imports(root):
    target = root / "tools" / "check_imports.py"
    make_backup(root, target)

    content = r'''from pathlib import Path
import py_compile
import importlib
import sys
import traceback


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


PROJECT_FILES = [
    "db.py",
    "keyboards.py",
    "handlers/start.py",
    "handlers/profile.py",
    "handlers/inventory.py",
    "handlers/combat.py",
    "handlers/city.py",
    "handlers/contracts.py",
    "handlers/guild.py",
    "handlers/auction_house.py",
    "systems/combat_system.py",
    "systems/refine_system.py",
    "systems/guild_system.py",
    "systems/auction_house_system.py",
]


SAFE_IMPORT_MODULES = [
    "db",
    "keyboards",
    "systems.combat_system",
    "systems.refine_system",
    "systems.guild_system",
    "systems.auction_house_system",
]


def print_header(title):
    print("=" * 80)
    print(title)
    print("=" * 80)


def compile_project_files():
    errors = []

    for relative_path in PROJECT_FILES:
        path = ROOT / relative_path

        if not path.exists():
            print(f"[SKIP] missing: {relative_path}")
            continue

        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as error:
            errors.append((relative_path, error))

    return errors


def import_safe_modules():
    errors = []

    for module_name in SAFE_IMPORT_MODULES:
        try:
            importlib.import_module(module_name)
            print(f"[OK] import {module_name}")
        except Exception as error:
            errors.append((module_name, error))

    return errors


def main():
    print_header("ROM compile/import check")

    compile_errors = compile_project_files()

    if compile_errors:
        print("[COMPILE ERRORS]")
        for path, error in compile_errors:
            print(f"- {path}: {error}")
    else:
        print("[OK] py_compile passed for project files.")

    print()
    print("[SAFE IMPORT CHECK]")

    import_errors = import_safe_modules()

    if import_errors:
        print()
        print("[IMPORT WARNINGS/ERRORS]")
        for module_name, error in import_errors:
            print(f"- {module_name}: {error}")
            traceback.print_exception(type(error), error, error.__traceback__)
    else:
        print()
        print("[OK] safe imports passed.")

    print()
    print("Note:")
    print("- main.py is intentionally not imported here, because importing main.py can start the bot.")
    print("- handlers are compiled, not imported, to avoid registering handlers during audit.")
    print()
    print("Done.")


if __name__ == "__main__":
    main()
'''

    target.write_text(content, encoding="utf-8")


def write_smoke_test(root):
    target = root / "tools" / "smoke_test_rom_core.py"
    make_backup(root, target)

    content = r'''from pathlib import Path
import sys
import traceback


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def print_header(title):
    print("=" * 80)
    print(title)
    print("=" * 80)


def run_check(name, func):
    try:
        result = func()
        print(f"[OK] {name}: {result}")
        return True
    except Exception as error:
        print(f"[FAIL] {name}")
        traceback.print_exception(type(error), error, error.__traceback__)
        return False


def main():
    print_header("ROM core smoke-test")

    ok = True

    def import_db():
        import db
        return "db imported"

    ok = run_check("import db", import_db) and ok

    import db

    def init_core_systems():
        if hasattr(db, "init_refine_system"):
            db.init_refine_system()

        if hasattr(db, "init_guild_system"):
            db.init_guild_system()

        if hasattr(db, "init_auction_house"):
            db.init_auction_house()

        return "core systems initialized"

    ok = run_check("init core systems", init_core_systems) and ok

    def check_known_user_queries():
        # Не вимагає існування конкретного користувача.
        # Просто перевіряє, що ключові функції доступні та не падають на імпорті.
        required_functions = [
            "create_user",
            "get_max_hp",
            "get_user_mp",
            "get_character_name",
            "get_character_class_display",
            "init_refine_system",
            "init_guild_system",
            "init_auction_house",
        ]

        missing = [
            name
            for name in required_functions
            if not hasattr(db, name)
        ]

        if missing:
            raise RuntimeError(f"Missing db API functions: {missing}")

        return "required db API functions exist"

    ok = run_check("required db API functions", check_known_user_queries) and ok

    print()
    if ok:
        print("[OK] ROM core smoke-test passed.")
    else:
        print("[FAIL] ROM core smoke-test failed.")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''

    target.write_text(content, encoding="utf-8")


def main():
    root = Path(__file__).resolve().parents[1]

    check_imports = root / "tools" / "check_imports.py"
    smoke_test = root / "tools" / "smoke_test_rom_core.py"

    if not check_imports.exists():
        raise SystemExit("❌ tools/check_imports.py не знайдено.")

    if not smoke_test.exists():
        raise SystemExit("❌ tools/smoke_test_rom_core.py не знайдено.")

    write_check_imports(root)
    write_smoke_test(root)

    py_compile.compile(str(check_imports), doraise=True)
    py_compile.compile(str(smoke_test), doraise=True)

    print("✅ Патч 9.0.0a застосовано успішно.")
    print("✅ tools/check_imports.py оновлено.")
    print("✅ tools/smoke_test_rom_core.py оновлено.")
    print("✅ Обидва tools пройшли py_compile.")
    print()
    print("Тепер запусти:")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")


if __name__ == "__main__":
    main()