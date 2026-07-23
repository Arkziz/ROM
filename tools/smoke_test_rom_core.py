from pathlib import Path
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
