from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_6a_auction_weapon_type_line_alias"
TARGET_RELATIVE = Path("systems") / "auction_house_system.py"
MARKER = "# ✅ ROM 9.0.6a AUCTION WEAPON TYPE LINE ALIAS V1"

APPEND_CODE = r'''

# ==============================
# ✅ ROM 9.0.6a AUCTION WEAPON TYPE LINE ALIAS V1
# ==============================

# Fix reason:
# build_auction_buy_lot_details_v2() calls _auction_inventory_style_weapon_type_line(snapshot),
# but in the current auction_house_system.py only _auction_inventory_style_type_line(snapshot)
# exists. This caused NameError when opening an equipment lot in Buy flow.
#
# This compatibility alias restores the expected function name without changing
# the auction item formatting logic.


def _auction_inventory_style_weapon_type_line(snapshot):
    """Compatibility wrapper for auction equipment details."""

    try:
        return _auction_inventory_style_type_line(snapshot)
    except NameError:
        return ""
    except Exception:
        return ""
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE

    if not target.exists():
        raise SystemExit(f"❌ Не знайдено файл: {target}")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ Патч уже застосовано раніше.")
        return

    backup = make_backup(root, target)

    try:
        target.write_text(original.rstrip() + "\n" + APPEND_CODE + "\n", encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_9_0_6a_auction_weapon_type_line_alias.\n"
            "Файл systems/auction_house_system.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.6a Auction weapon type line alias застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ systems/auction_house_system.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- додано _auction_inventory_style_weapon_type_line(snapshot)")
    print("- функція делегує форматування на існуючу _auction_inventory_style_type_line(snapshot)")
    print("- відкриття спорядження в покупці Торгового Дому більше не має падати з NameError")


if __name__ == "__main__":
    main()
