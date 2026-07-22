from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_5c_auction_snapshot_weapon_details"
TARGET_REL = Path("systems") / "auction_house_system.py"
MARKER = "# ✅ AUCTION HOUSE SNAPSHOT WEAPON DETAILS V1"

APPEND_CODE = r'''

# ==============================
# ✅ AUCTION HOUSE SNAPSHOT WEAPON DETAILS V1
# ==============================


def _auction_enrich_equipment_snapshot_with_runtime_details(user_id, inventory_id, snapshot):
    """
    Adds computed runtime details before the item is removed from inventory.

    Important: weapon damage in ROM is calculated by helpers and refine modifiers,
    so raw item columns are not always enough for Auction House details.
    """

    snapshot = dict(snapshot or {})

    try:
        from db import get_weapon_damage_by_inventory_id
        weapon_damage = get_weapon_damage_by_inventory_id(int(inventory_id))
        if isinstance(weapon_damage, dict) and weapon_damage.get("is_weapon"):
            snapshot["auction_weapon_damage"] = weapon_damage
    except Exception as error:
        snapshot["auction_weapon_damage_error"] = str(error)

    return snapshot


def _auction_damage_lines_from_weapon_damage_dict(weapon_damage):
    lines = []
    if not isinstance(weapon_damage, dict):
        return lines

    text = weapon_damage.get("text")
    if text:
        lines.append(str(text))
        return lines

    pmin = _auction_int_or_none(weapon_damage.get("physical_min"))
    pmax = _auction_int_or_none(weapon_damage.get("physical_max"))
    mmin = _auction_int_or_none(weapon_damage.get("magic_min"))
    mmax = _auction_int_or_none(weapon_damage.get("magic_max"))

    if pmin is not None and pmax is not None and (pmin > 0 or pmax > 0):
        lines.append(f"⚔️ Фіз. шкода: {pmin}-{pmax}")

    if mmin is not None and mmax is not None and (mmin > 0 or mmax > 0):
        lines.append(f"🔮 Маг. шкода: {mmin}-{mmax}")

    return lines


def create_equipment_auction_lot(user_id, inventory_id, price):
    """
    Replaces 8.0.3 equipment listing with snapshot enrichment.

    The item is still moved out of inventory into auction_lots, but before deletion
    we store computed weapon damage / refine-aware details into item_snapshot_json.
    """

    init_auction_house()

    check = validate_inventory_item_for_auction_equipment(user_id, inventory_id)

    if not check.get("success"):
        return check

    can_create = can_user_create_auction_lot(user_id)
    if not can_create.get("success"):
        return can_create

    price_result = validate_auction_price(price)
    if not price_result.get("success"):
        return price_result

    now = now_iso()
    expires_at = iso_after_days(AUCTION_ACTIVE_DAYS)

    try:
        conn.execute("BEGIN IMMEDIATE")

        check_inside = validate_inventory_item_for_auction_equipment(user_id, inventory_id)
        if not check_inside.get("success"):
            conn.rollback()
            return check_inside

        snapshot = check_inside["snapshot"]
        snapshot = _auction_enrich_equipment_snapshot_with_runtime_details(user_id, inventory_id, snapshot)

        cursor.execute("""
        INSERT INTO auction_lots (
            seller_user_id,
            buyer_user_id,
            item_type,
            item_source,
            item_ref_id,
            item_snapshot_json,
            item_name,
            item_name_norm,
            category,
            rarity,
            level,
            enhancement_level,
            durability_current,
            durability_max,
            quantity,
            price,
            status,
            created_at,
            expires_at,
            updated_at
        ) VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            snapshot.get("item_type") or "equipment",
            "inventory",
            int(inventory_id),
            safe_json_dumps(snapshot),
            snapshot["name"],
            snapshot["name"].lower(),
            AUCTION_CATEGORY_EQUIPMENT,
            snapshot.get("rarity", ""),
            int(snapshot.get("level", 0) or 0),
            int(snapshot.get("refine_level", 0) or 0),
            snapshot.get("durability_current"),
            snapshot.get("durability_max"),
            1,
            price_result["price"],
            AUCTION_STATUS_ACTIVE,
            now,
            expires_at,
            now,
        ))

        lot_id = cursor.lastrowid

        cursor.execute(
            "DELETE FROM inventory WHERE id=? AND user_id=?",
            (inventory_id, user_id)
        )

        if cursor.rowcount != 1:
            conn.rollback()
            return {
                "success": False,
                "message": "❌ Не вдалося перенести предмет з інвентаря.",
            }

        cursor.execute("""
        INSERT INTO auction_history (
            lot_id,
            event_type,
            actor_user_id,
            seller_user_id,
            buyer_user_id,
            item_name,
            category,
            quantity,
            price,
            status_before,
            status_after,
            details_json,
            created_at
        ) VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, NULL, ?, ?, ?)
        """, (
            lot_id,
            AUCTION_HISTORY_LISTED,
            user_id,
            user_id,
            snapshot["name"],
            AUCTION_CATEGORY_EQUIPMENT,
            1,
            price_result["price"],
            AUCTION_STATUS_ACTIVE,
            safe_json_dumps({
                "inventory_id": inventory_id,
                "item_id": snapshot.get("item_id"),
                "runtime_details": "weapon_damage_snapshot_v1",
            }),
            now,
        ))

        conn.commit()

        return {
            "success": True,
            "lot_id": lot_id,
            "item_name": snapshot["name"],
            "price": price_result["price"],
            "expires_at": expires_at,
            "message": "✅ Лот виставлено на продаж.",
        }

    except Exception as error:
        try:
            conn.rollback()
        except Exception:
            pass

        return {
            "success": False,
            "message": f"❌ Помилка створення лота: {error}",
        }


def build_auction_lot_public_details(lot_id, viewer_user_id=None):
    """
    Richer buyer item card.

    Uses runtime weapon damage snapshot for new equipment lots, so the Auction House
    card is closer to the normal inventory item details.
    """

    init_auction_house()
    lot = get_auction_lot_by_id(lot_id)

    if not lot:
        return {
            "success": False,
            "message": "❌ Лот не знайдено.",
        }

    if lot["status"] != AUCTION_STATUS_ACTIVE:
        return {
            "success": False,
            "message": "⚠️ Лот уже недоступний.",
        }

    snapshot = safe_json_loads(lot["item_snapshot_json"])

    category = lot["category"]
    quantity = int(lot["quantity"] or 1)
    refine_level = int(lot["enhancement_level"] or snapshot.get("refine_level", 0) or 0)
    item_type = snapshot.get("item_type") or _auction_snapshot_value(snapshot, "type", "item_type", default="")
    slot_key = snapshot.get("slot_key") or _auction_snapshot_value(snapshot, "slot_key", "slot", default="")
    rarity = lot["rarity"] or snapshot.get("rarity") or _auction_snapshot_value(snapshot, "rarity", default="")
    level = int(lot["level"] or snapshot.get("level", 0) or 0)

    lines = []
    lines.append("📦 Лот Торгового Дому")
    lines.append("")
    lines.append(str(lot["item_name"]))
    lines.append("")

    lines.append(f"📂 Категорія: {_auction_category_ua(category)}")

    if category == AUCTION_CATEGORY_EQUIPMENT:
        lines.append(f"🎒 Слот/тип: {_auction_slot_ua(slot_key, item_type)}")
        if rarity:
            lines.append(f"⭐ Рідкість: {_auction_rarity_ua(rarity)}")
        if level:
            lines.append(f"🏷 Рівень: {level}")
        if refine_level:
            lines.append(f"✨ Заточка: +{refine_level}")
        if lot["durability_current"] is not None:
            lines.append(f"🔧 Міцність: {lot['durability_current']}/{lot['durability_max']}")

        damage_lines = _auction_damage_lines_from_weapon_damage_dict(snapshot.get("auction_weapon_damage"))
        if not damage_lines:
            damage_lines = _auction_collect_damage_lines(snapshot)

        stat_lines = _auction_collect_equipment_stat_lines(snapshot)

        if damage_lines:
            lines.append("")
            lines.append("— Шкода —")
            lines.extend(damage_lines)

        if stat_lines:
            lines.append("")
            lines.append("— Бонуси предмета —")
            lines.extend(stat_lines)

        if not damage_lines and not stat_lines:
            lines.append("")
            lines.append("ℹ️ Детальні стати для цього предмета не знайдені у snapshot лота.")
            lines.append("Нові лоти, виставлені після 8.0.5c, зберігатимуть більше бойових даних.")

    else:
        lines.append(f"📦 Кількість: {quantity}")
        desc_lines = _auction_collect_stack_description_lines(snapshot)
        if desc_lines:
            lines.append("")
            lines.extend(desc_lines)

    lines.append("")
    lines.append(f"💰 Ціна: {lot['price']} золота")
    lines.append("⏳ Активний лот: до 7 днів від створення")
    lines.append("")
    lines.append("Продавець прихований.")

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
    target = root / TARGET_REL

    if not target.exists():
        raise SystemExit("❌ Не знайдено systems/auction_house_system.py. Спочатку потрібні патчі 8.0.1-8.0.5b.")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ Патч 8.0.5c вже застосовано. Змін не потрібно.")
        py_compile.compile(str(target), doraise=True)
        return

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + APPEND_CODE + "\n", encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_8_0_5c_auction_snapshot_weapon_details.\n"
            "systems/auction_house_system.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.5c Auction snapshot weapon details застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ systems/auction_house_system.py пройшов py_compile.")
    print("\nЩо змінено:")
    print("- при виставленні спорядження snapshot тепер зберігає runtime weapon damage")
    print("- перегляд лота показує шкоду зброї з get_weapon_damage_by_inventory_id")
    print("- картка лота ближча до деталей предмета в інвентарі")
    print("\nВажливо:")
    print("- старі лоти, створені до 8.0.5c, можуть не мати збереженої шкоди")
    print("- для повної перевірки вистав новий жезл/посох після цього патча")
    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
