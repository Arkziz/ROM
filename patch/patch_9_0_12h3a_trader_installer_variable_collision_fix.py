from pathlib import Path
from datetime import datetime
import py_compile
import runpy

PATCH_NAME = "9_0_12h3a_trader_installer_variable_collision_fix"
BROKEN_INSTALLER = "patch_9_0_12h3_equipment_trader_real_implementation.py"


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = backup_dir / f"{target.name}_{PATCH_NAME}_{stamp}.bak"
    dst.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return dst


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Не вдалося однозначно виправити {label}: знайдено входжень {count}.")
    return text.replace(old, new, 1)


def main():
    root = Path(__file__).resolve().parents[1]
    installer = root / "patch" / BROKEN_INSTALLER
    equipment = root / "systems" / "equipment_system.py"

    if not installer.exists():
        raise SystemExit(f"❌ Не знайдено початковий патч: {installer}")
    if not equipment.exists():
        raise SystemExit(f"❌ Не знайдено файл: {equipment}")

    source = installer.read_text(encoding="utf-8")
    fixed_marker = "# 9.0.12h3 INSTALLER VARIABLE COLLISION FIXED"

    if fixed_marker not in source:
        backup_path = make_backup(root, installer)
        fixed = source
        fixed = replace_once(
            fixed,
            'SMOKE = Path("tools") / "smoke_test_equipment_trader_contracts.py"',
            'SMOKE_PATH = Path("tools") / "smoke_test_equipment_trader_contracts.py"',
            "константу шляху SMOKE",
        )
        fixed = replace_once(
            fixed,
            "SMOKE = r'''from pathlib import Path",
            "SMOKE_CODE = r'''from pathlib import Path",
            "текст smoke-test",
        )
        fixed = replace_once(
            fixed,
            "smoke = root / SMOKE\n",
            "smoke = root / SMOKE_PATH\n",
            "побудову шляху smoke-test",
        )
        fixed = replace_once(
            fixed,
            "smoke.write_text(SMOKE, encoding=\"utf-8\")",
            "smoke.write_text(SMOKE_CODE, encoding=\"utf-8\")",
            "запис smoke-test",
        )
        fixed = fixed_marker + "\n" + fixed
        installer.write_text(fixed, encoding="utf-8")
        py_compile.compile(str(installer), doraise=True)
        print("✅ Конфлікт змінної SMOKE у патчі 9.0.12h3 виправлено.")
        print(f"Резервна копія: {backup_path}")
    else:
        print("ℹ️ Інсталятор 9.0.12h3 уже виправлено.")

    # The failed installer restored equipment_system.py before its cleanup error,
    # so executing the corrected installer is safe and idempotent.
    print("▶️ Повторне застосування виправленого патча 9.0.12h3...")
    runpy.run_path(str(installer), run_name="__main__")


if __name__ == "__main__":
    main()
