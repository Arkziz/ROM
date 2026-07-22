from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_5b_auction_lot_details_stats"
TARGET_REL = Path("systems") / "auction_house_system.py"
MARKER = "# ✅ AUCTION HOUSE LOT DETAILS STATS V1"

APPEND_CODE = r'''

# ==============================
# ✅ AUCTION HOUSE LOT DETAILS STATS V1
# ==============================


def _auction_snapshot_value(snapshot, *names, default=None):
    """Read value from snapshot or its saved row aliases."""

    row = snapshot.get("row") or {}

    for name in names:
        if name in snapshot and snapshot.get(name) not in [None, ""]:
            return snapshot.get(name)

    candidates = []
    for name in names:
        candidates.extend([
            name,
            f"item_{name}",
            f"inv_{name}",
        ])

    for name in candidates:
        if name in row and row.get(name) not in [None, ""]:
            return row.get(name)

    return default


def _auction_int_or_none(value):
    if value in [None, ""]:
        return None
    try:
        return int(value)
    except Exception:
        try:
            return int(float(value))
        except Exception:
            return None


def _auction_add_stat_line(lines, label, value, prefix="+"):
    value = _auction_int_or_none(value)
    if value is None or value == 0:
        return
    sign = prefix if value > 0 else ""
    lines.append(f"{label} {sign}{value}")


def _auction_rarity_ua(rarity):
    rarity = str(rarity or "").lower()
    mapping = {
        "common": "⚪ Звичайна",
        "uncommon": "🟢 Незвичайна",
        "rare": "🔵 Рідкісна",
        "epic": "🟣 Епічна",
        "grey": "⚫ Сіра",
    }
    return mapping.get(rarity, rarity or "—")


def _auction_category_ua(category):
    category = str(category or "").lower()
    mapping = {
        AUCTION_CATEGORY_EQUIPMENT: "⚔️ Спорядження",
        AUCTION_CATEGORY_POTION: "🧪 Зілля",
        AUCTION_CATEGORY_MATERIAL: "🪨 Матеріали",
    }
    return mapping.get(category, category or "—")


def _auction_slot_ua(slot_key, item_type=""):
    slot_key = str(slot_key or "").lower()
    item_type = str(item_type or "").lower()
    value = slot_key or item_type

    mapping = {
        "main_hand": "Основна рука",
        "off_hand": "Друга рука",
        "weapon": "Зброя",
        "helmet": "Шолом",
        "shoulders": "Плечі",
        "chest": "Обладунок",
        "gloves": "Рукавиці",
        "legs": "Поножі",
        "boots": "Чоботи",
        "necklace": "Намисто",
        "ring": "Перстень",
    }
    return mapping.get(value, value or "—")


def _auction_collect_damage_lines(snapshot):
    lines = []

    physical_min = _auction_snapshot_value(snapshot, "physical_min", "phys_min", "damage_min", "attack_min")
    physical_max = _auction_snapshot_value(snapshot, "physical_max", "phys_max", "damage_max", "attack_max")
    magic_min = _auction_snapshot_value(snapshot, "magic_min", "magical_min", "magic_damage_min")
    magic_max = _auction_snapshot_value(snapshot, "magic_max", "magical_max", "magic_damage_max")

    pmin = _auction_int_or_none(physical_min)
    pmax = _auction_int_or_none(physical_max)
    mmin = _auction_int_or_none(magic_min)
    mmax = _auction_int_or_none(magic_max)

    if pmin is not None and pmax is not None and (pmin > 0 or pmax > 0):
        lines.append(f"⚔️ Фіз. шкода: {pmin}-{pmax}")

    if mmin is not None and mmax is not None and (mmin > 0 or mmax > 0):
        lines.append(f"🔮 Маг. шкода: {mmin}-{mmax}")

    # Fallback for DBs that store one damage pair only.
    if not lines:
        dmg_min = _auction_snapshot_value(snapshot, "min_damage", "damage_min")
        dmg_max = _auction_snapshot_value(snapshot, "max_damage", "damage_max")
        dmin = _auction_int_or_none(dmg_min)
        dmax = _auction_int_or_none(dmg_max)
        if dmin is not None and dmax is not None and (dmin > 0 or dmax > 0):
            lines.append(f"⚔️ Шкода: {dmin}-{dmax}")

    return lines


def _auction_collect_equipment_stat_lines(snapshot):
    lines = []

    _auction_add_stat_line(lines, "PDEF", _auction_snapshot_value(snapshot, "pdef", "physical_defense"))
    _auction_add_stat_line(lines, "MDEF", _auction_snapshot_value(snapshot, "mdef", "magic_defense", "magical_defense"))

    _auction_add_stat_line(lines, "STR", _auction_snapshot_value(snapshot, "bonus_str", "str", "strength"))
    _auction_add_stat_line(lines, "DEX", _auction_snapshot_value(snapshot, "bonus_dex", "dex", "dexterity"))
    _auction_add_stat_line(lines, "INT", _auction_snapshot_value(snapshot, "bonus_int", "int", "intelligence"))
    _auction_add_stat_line(lines, "WIS", _auction_snapshot_value(snapshot, "bonus_wis", "wis", "wisdom"))
    _auction_add_stat_line(lines, "STA", _auction_snapshot_value(snapshot, "bonus_sta", "sta", "stamina"))

    return lines


def _auction_collect_stack_description_lines(snapshot):
    lines = []
    item_id = _auction_int_or_none(snapshot.get("item_id"))
    name = str(snapshot.get("name") or snapshot.get("raw_name") or "")

    if item_id == 401 or "Камінь Посилення" in name:
        lines.append("ℹ️ Використовується у Коваля для спроби заточки спорядження.")
        lines.append("• Витрачається при кожній спробі заточки.")
        lines.append("• Не гарантує успіх.")
    elif "зіл" in name.lower() or "potion" in name.lower():
        lines.append("ℹ️ Витратний предмет, який можна використовувати поза Торговим Домом після купівлі.")

    return lines


def build_auction_lot_public_details(lot_id, viewer_user_id=None):
    """
    Rich public lot details for buyers.

    Seller remains hidden. Shows stats saved in item snapshot: damage, defenses,
    attributes, refine level, durability, quantity and price.
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
            lines.append("Якщо цей лот був створений старішим патчем, нові лоти будуть показувати більше даних.")

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
        raise SystemExit("❌ Не знайдено systems/auction_house_system.py. Спочатку потрібні патчі 8.0.1-8.0.5.")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ Патч 8.0.5b вже застосовано. Змін не потрібно.")
        py_compile.compile(str(target), doraise=True)
        return

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + APPEND_CODE + "\n", encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_8_0_5b_auction_lot_details_stats.\n"
            "systems/auction_house_system.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.5b Auction lot details stats застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ systems/auction_house_system.py пройшов py_compile.")
    print("\nЩо додано:")
    print("- детальніший перегляд лота")
    print("- слот/тип предмета")
    print("- рідкість")
    print("- шкода зброї, якщо є у snapshot")
    print("- PDEF/MDEF")
    print("- STR/DEX/INT/WIS/STA бонуси")
    print("- опис для матеріалів, зокрема 🪨 Каменя Посилення")
    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
