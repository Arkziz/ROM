from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_8a_auction_ua_date_format"
TARGET_RELATIVE = Path("systems") / "auction_house_system.py"
MARKER = "# ✅ AUCTION HOUSE UA DATE FORMAT V1"

APPEND_CODE = r'''

# ==============================
# ✅ AUCTION HOUSE UA DATE FORMAT V1
# ==============================


def _auction_format_ua_datetime_v1(value, with_time=True):
    """
    Formats ISO datetime values for Ukrainian UI.

    Examples:
    2026-07-23T00:07:18.129143 -> 23.07.2026 00:07
    2026-08-22T00:07:18.129168 -> 22.08.2026 00:07
    """

    if not value:
        return "-"

    text = str(value).strip()

    try:
        normalized = text.replace("Z", "").replace(" ", "T")
        dt = datetime.fromisoformat(normalized)

        if with_time:
            return dt.strftime("%d.%m.%Y %H:%M")

        return dt.strftime("%d.%m.%Y")

    except Exception:
        pass

    # Fallback for YYYY-MM-DD or strings starting with a date.
    try:
        if len(text) >= 10 and text[4] == "-" and text[7] == "-":
            yyyy = text[0:4]
            mm = text[5:7]
            dd = text[8:10]

            if with_time and len(text) >= 16:
                hh = text[11:13]
                minute = text[14:16]
                if hh.isdigit() and minute.isdigit():
                    return f"{dd}.{mm}.{yyyy} {hh}:{minute}"

            return f"{dd}.{mm}.{yyyy}"

    except Exception:
        pass

    return text


def build_user_unclaimed_auction_sale_details(user_id, lot_id):
    """
    Ukrainian date-format override for completed sales details.
    """

    init_auction_house()
    update_expired_auction_lots()

    cursor.execute(
        "SELECT * FROM auction_lots WHERE id=? AND seller_user_id=?",
        (int(lot_id), int(user_id))
    )
    lot = cursor.fetchone()

    if not lot:
        return {"success": False, "message": "❌ Продаж не знайдено."}

    if lot["status"] != AUCTION_STATUS_SOLD_UNCLAIMED:
        return {"success": False, "message": "⚠️ Це золото вже отримано або продаж недоступний."}

    snapshot = safe_json_loads(lot["item_snapshot_json"])
    category = lot["category"]
    quantity = int(lot["quantity"] or 1)

    lines = []
    lines.append("💰 Завершений продаж")
    lines.append("")
    lines.append(str(lot["item_name"]))
    lines.append("")
    lines.append(f"✅ Продано за: {lot['price']} золота")

    if lot["sold_at"]:
        lines.append(f"🕒 Дата продажу: {_auction_format_ua_datetime_v1(lot['sold_at'], with_time=True)}")
    if lot["delete_after"]:
        lines.append(f"🗑 Видалення виплати після: {_auction_format_ua_datetime_v1(lot['delete_after'], with_time=True)}")

    if category == AUCTION_CATEGORY_EQUIPMENT:
        refine_level = int(lot["enhancement_level"] or snapshot.get("refine_level", 0) or 0)
        item_type = snapshot.get("item_type") or _auction_snapshot_value(snapshot, "type", "item_type", default="")
        slot_key = snapshot.get("slot_key") or _auction_snapshot_value(snapshot, "slot_key", "slot", default="")
        level = int(lot["level"] or snapshot.get("level", 0) or 0)

        lines.append("")
        lines.append(_auction_inventory_style_type_line(AUCTION_CATEGORY_EQUIPMENT))
        lines.append(f"🎯 Слот: {_auction_inventory_style_slot(snapshot, slot_key, item_type)}")
        if level:
            lines.append(f"🏷 Рівень предмета: {level} 🔒")
        if refine_level:
            lines.append(f"✨ Заточка: +{refine_level}")
        if lot["durability_current"] is not None:
            lines.append(f"🧱 Міцність: {lot['durability_current']}/{lot['durability_max']}")

        damage_lines = _auction_inventory_style_damage_lines(snapshot)
        defense_lines = _auction_collect_inventory_style_defense_lines(snapshot)
        bonus_lines = _auction_collect_inventory_style_bonus_lines(snapshot)

        if damage_lines:
            lines.append("")
            lines.extend(damage_lines)
        if defense_lines:
            lines.extend(defense_lines)
        if bonus_lines:
            lines.append("")
            lines.append("📊 Бонуси:")
            lines.extend(bonus_lines)
    else:
        lines.append("")
        lines.append(_auction_inventory_style_type_line(category))
        lines.append(f"📦 Кількість: {quantity}")
        desc_lines = _auction_collect_stack_description_lines(snapshot)
        if desc_lines:
            lines.append("")
            lines.extend(desc_lines)

    lines.append("")
    lines.append("Золото можна забрати вручну.")

    return {
        "success": True,
        "lot": lot,
        "snapshot": snapshot,
        "text": "\n".join(lines),
    }


def build_user_unclaimed_auction_item_details(user_id, lot_id):
    """
    Ukrainian date-format override for expired unclaimed item details.
    """

    init_auction_house()
    update_expired_auction_lots()

    cursor.execute(
        "SELECT * FROM auction_lots WHERE id=? AND seller_user_id=?",
        (int(lot_id), int(user_id))
    )
    lot = cursor.fetchone()

    if not lot:
        return {"success": False, "message": "❌ Лот не знайдено."}

    if lot["status"] != AUCTION_STATUS_EXPIRED_UNCLAIMED:
        return {"success": False, "message": "⚠️ Цей предмет уже не очікує отримання."}

    snapshot = safe_json_loads(lot["item_snapshot_json"])
    category = lot["category"]
    quantity = int(lot["quantity"] or 1)

    lines = []
    lines.append("📬 Незабраний предмет")
    lines.append("")
    lines.append(str(lot["item_name"]))
    lines.append("")
    lines.append("⏳ Лот завершився і не був проданий.")
    lines.append(f"💰 Ціна лота була: {lot['price']} золота")

    if lot["delete_after"]:
        lines.append(f"🗑 Видалення після: {_auction_format_ua_datetime_v1(lot['delete_after'], with_time=True)}")

    if category == AUCTION_CATEGORY_EQUIPMENT:
        refine_level = int(lot["enhancement_level"] or snapshot.get("refine_level", 0) or 0)
        item_type = snapshot.get("item_type") or _auction_snapshot_value(snapshot, "type", "item_type", default="")
        slot_key = snapshot.get("slot_key") or _auction_snapshot_value(snapshot, "slot_key", "slot", default="")
        level = int(lot["level"] or snapshot.get("level", 0) or 0)

        lines.append("")
        lines.append(_auction_inventory_style_type_line(AUCTION_CATEGORY_EQUIPMENT))
        lines.append(f"🎯 Слот: {_auction_inventory_style_slot(snapshot, slot_key, item_type)}")
        if level:
            lines.append(f"🏷 Рівень предмета: {level} 🔒")
        if refine_level:
            lines.append(f"✨ Заточка: +{refine_level}")
        if lot["durability_current"] is not None:
            lines.append(f"🧱 Міцність: {lot['durability_current']}/{lot['durability_max']}")

        damage_lines = _auction_inventory_style_damage_lines(snapshot)
        defense_lines = _auction_collect_inventory_style_defense_lines(snapshot)
        bonus_lines = _auction_collect_inventory_style_bonus_lines(snapshot)

        if damage_lines:
            lines.append("")
            lines.extend(damage_lines)
        if defense_lines:
            lines.extend(defense_lines)
        if bonus_lines:
            lines.append("")
            lines.append("📊 Бонуси:")
            lines.extend(bonus_lines)
    else:
        lines.append("")
        lines.append(_auction_inventory_style_type_line(category))
        lines.append(f"📦 Кількість: {quantity}")
        desc_lines = _auction_collect_stack_description_lines(snapshot)
        if desc_lines:
            lines.append("")
            lines.extend(desc_lines)

    lines.append("")
    lines.append("Предмет можна повернути в інвентар, якщо там є місце.")

    return {
        "success": True,
        "lot": lot,
        "snapshot": snapshot,
        "text": "\n".join(lines),
    }
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
            "❌ Помилка компіляції після patch_8_0_8a_auction_ua_date_format.\n"
            "Файл відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.8a Auction UA date format застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ systems/auction_house_system.py пройшов py_compile.")
    print("")
    print("Що змінено:")
    print("- Дата продажу показується як DD.MM.YYYY HH:MM")
    print("- Дата видалення виплати показується як DD.MM.YYYY HH:MM")
    print("- Дата видалення незабраного предмета теж показується як DD.MM.YYYY HH:MM")


if __name__ == "__main__":
    main()
