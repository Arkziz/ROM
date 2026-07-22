from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_5d_auction_lot_details_inventory_style"
TARGET_REL = Path("systems") / "auction_house_system.py"
MARKER = "# ✅ AUCTION HOUSE INVENTORY STYLE LOT DETAILS V1"

APPEND_CODE = r'''

# ==============================
# ✅ AUCTION HOUSE INVENTORY STYLE LOT DETAILS V1
# ==============================


def _auction_ua_stat_label(stat_key):
    stat_key = str(stat_key or "").lower()
    mapping = {
        "str": ("💪", "Сила"),
        "strength": ("💪", "Сила"),
        "bonus_str": ("💪", "Сила"),
        "dex": ("🎯", "Спритність"),
        "dexterity": ("🎯", "Спритність"),
        "bonus_dex": ("🎯", "Спритність"),
        "int": ("🔮", "Інтелект"),
        "intelligence": ("🔮", "Інтелект"),
        "bonus_int": ("🔮", "Інтелект"),
        "wis": ("🦉", "Мудрість"),
        "wisdom": ("🦉", "Мудрість"),
        "bonus_wis": ("🦉", "Мудрість"),
        "sta": ("🛡", "Витривалість"),
        "stamina": ("🛡", "Витривалість"),
        "bonus_sta": ("🛡", "Витривалість"),
    }
    return mapping.get(stat_key, ("•", stat_key.upper()))


def _auction_ua_stat_value(snapshot, *keys):
    for key in keys:
        value = _auction_snapshot_value(snapshot, key)
        value = _auction_int_or_none(value)
        if value is not None and value != 0:
            return key, value
    return None, None


def _auction_collect_inventory_style_bonus_lines(snapshot):
    stat_groups = [
        ("bonus_str", "str", "strength"),
        ("bonus_dex", "dex", "dexterity"),
        ("bonus_int", "int", "intelligence"),
        ("bonus_wis", "wis", "wisdom"),
        ("bonus_sta", "sta", "stamina"),
    ]

    lines = []
    for group in stat_groups:
        key, value = _auction_ua_stat_value(snapshot, *group)
        if key is None:
            continue
        icon, label = _auction_ua_stat_label(key)
        sign = "+" if value > 0 else ""
        lines.append(f"• {icon} {label} {sign}{value}")

    return lines


def _auction_collect_inventory_style_defense_lines(snapshot):
    lines = []

    pdef = _auction_snapshot_value(snapshot, "pdef", "physical_defense")
    mdef = _auction_snapshot_value(snapshot, "mdef", "magic_defense", "magical_defense")

    pdef = _auction_int_or_none(pdef)
    mdef = _auction_int_or_none(mdef)

    if pdef is not None and pdef != 0:
        lines.append(f"🛡 Фіз. захист: +{pdef}" if pdef > 0 else f"🛡 Фіз. захист: {pdef}")
    if mdef is not None and mdef != 0:
        lines.append(f"🔮 Маг. захист: +{mdef}" if mdef > 0 else f"🔮 Маг. захист: {mdef}")

    return lines


def _auction_inventory_style_slot(snapshot, slot_key, item_type):
    slot_key_l = str(slot_key or "").lower()
    item_type_l = str(item_type or "").lower()
    value = slot_key_l or item_type_l

    mapping = {
        "main_hand": "🗡️ Зброя",
        "weapon": "🗡️ Зброя",
        "off_hand": "🛡️ Друга рука",
        "shield": "🛡️ Щит",
        "helmet": "🪖 Шолом",
        "shoulders": "🎽 Плечі",
        "chest": "🥋 Обладунок",
        "gloves": "🧤 Рукавиці",
        "legs": "👖 Поножі",
        "boots": "🥾 Чоботи",
        "necklace": "📿 Намисто",
        "ring": "💍 Перстень",
    }

    return mapping.get(value, _auction_slot_ua(slot_key, item_type))


def _auction_inventory_style_type_line(category):
    if category == AUCTION_CATEGORY_EQUIPMENT:
        return "🧰 Тип: спорядження"
    if category == AUCTION_CATEGORY_POTION:
        return "🧰 Тип: зілля"
    if category == AUCTION_CATEGORY_MATERIAL:
        return "🧰 Тип: матеріал"
    return f"🧰 Тип: {category}"


def _auction_class_icon_name(value):
    value = str(value or "").strip().lower()
    aliases = {
        "mage": "🔮 Маг",
        "mag": "🔮 Маг",
        "wizard": "🔮 Маг",
        "priest": "⚕️ Жрець",
        "healer": "⚕️ Жрець",
        "cleric": "⚕️ Жрець",
        "warrior": "⚔️ Воїн",
        "fighter": "⚔️ Воїн",
        "rogue": "🗡️ Розбійник",
        "assassin": "🗡️ Розбійник",
        "hunter": "🏹 Мисливець",
        "ranger": "🏹 Мисливець",
        "маг": "🔮 Маг",
        "жрець": "⚕️ Жрець",
        "воїн": "⚔️ Воїн",
        "розбійник": "🗡️ Розбійник",
        "мисливець": "🏹 Мисливець",
    }
    return aliases.get(value, None)


def _auction_allowed_classes_line(snapshot):
    raw = None
    for key in ["allowed_classes", "classes", "class_allowed", "required_classes", "required_class", "class_restriction"]:
        raw = _auction_snapshot_value(snapshot, key)
        if raw not in [None, ""]:
            break

    if raw in [None, ""]:
        # Heuristic fallback for common weapon restrictions if explicit class data is absent.
        name = str(snapshot.get("name") or snapshot.get("raw_name") or "").lower()
        item_type = str(snapshot.get("item_type") or "").lower()
        slot_key = str(snapshot.get("slot_key") or "").lower()

        if "жезл" in name or "посох" in name or item_type in ["staff", "wand"]:
            classes = ["🔮 Маг", "⚕️ Жрець"]
        elif "лук" in name or item_type in ["bow"]:
            classes = ["🏹 Мисливець"]
        elif "киндж" in name or item_type in ["dagger"]:
            classes = ["🗡️ Розбійник"]
        elif slot_key == "main_hand" or item_type in ["weapon", "sword", "axe", "mace"]:
            classes = []
        else:
            classes = []
    else:
        if isinstance(raw, (list, tuple, set)):
            parts = list(raw)
        else:
            raw_text = str(raw).replace(";", ",").replace("/", ",").replace("|", ",")
            parts = [p.strip() for p in raw_text.split(",") if p.strip()]
        classes = []
        for part in parts:
            mapped = _auction_class_icon_name(part)
            if mapped and mapped not in classes:
                classes.append(mapped)

    if not classes:
        return None

    return "👥 Підходить класам: " + ", ".join(classes)


def _auction_weapon_hand_line(snapshot):
    name = str(snapshot.get("name") or snapshot.get("raw_name") or "").lower()
    item_type = str(snapshot.get("item_type") or "").lower()

    two_handed_raw = _auction_snapshot_value(snapshot, "two_handed", "is_two_handed", "requires_two_hands", "twohanded")
    hands_raw = _auction_snapshot_value(snapshot, "hands", "weapon_hands", "handedness")

    two_handed = False
    if str(two_handed_raw).lower() in ["1", "true", "yes", "так"]:
        two_handed = True
    if str(hands_raw).lower() in ["2", "two", "two_handed", "2h", "дворучна", "дворучний"]:
        two_handed = True
    if "дворуч" in name:
        two_handed = True

    is_weapon = bool(
        snapshot.get("auction_weapon_damage")
        or item_type in ["weapon", "staff", "wand", "sword", "axe", "mace", "dagger", "bow"]
        or "жезл" in name
        or "посох" in name
        or "меч" in name
        or "сокир" in name
        or "киндж" in name
        or "лук" in name
    )

    if not is_weapon:
        return None

    return "✋ Тип зброї: дворучна" if two_handed else "✋ Тип зброї: одноручна"


def _auction_inventory_style_damage_lines(snapshot):
    lines = _auction_damage_lines_from_weapon_damage_dict(snapshot.get("auction_weapon_damage"))
    if not lines:
        lines = _auction_collect_damage_lines(snapshot)

    # Normalize labels if runtime helper returns compact text.
    normalized = []
    for line in lines:
        line = str(line)
        line = line.replace("Фіз. шкода", "Фіз. шкода")
        line = line.replace("Маг. шкода", "Маг. шкода")
        normalized.append(line)
    return normalized


def build_auction_lot_public_details(lot_id, viewer_user_id=None):
    """
    Inventory-style public lot card.

    Same idea as item details in inventory, but without player-specific equip warnings:
    - no current player level;
    - no 'you can equip from level X' warning;
    - seller remains hidden.
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
    level = int(lot["level"] or snapshot.get("level", 0) or 0)

    lines = []
    lines.append("📦 Лот Торгового Дому")
    lines.append("")
    lines.append(str(lot["item_name"]))
    lines.append("")

    lines.append(_auction_inventory_style_type_line(category))

    if category == AUCTION_CATEGORY_EQUIPMENT:
        lines.append(f"🎯 Слот: {_auction_inventory_style_slot(snapshot, slot_key, item_type)}")

        class_line = _auction_allowed_classes_line(snapshot)
        if class_line:
            lines.append(class_line)

        if level:
            lines.append(f"🏷 Рівень предмета: {level} 🔒")

        weapon_hand_line = _auction_weapon_hand_line(snapshot)
        if weapon_hand_line:
            lines.append(weapon_hand_line)

        damage_lines = _auction_inventory_style_damage_lines(snapshot)
        for damage_line in damage_lines:
            lines.append(damage_line)

        defense_lines = _auction_collect_inventory_style_defense_lines(snapshot)
        for defense_line in defense_lines:
            lines.append(defense_line)

        if lot["durability_current"] is not None:
            lines.append(f"🧱 Міцність: {lot['durability_current']}/{lot['durability_max']}")

        bonus_lines = _auction_collect_inventory_style_bonus_lines(snapshot)
        if bonus_lines:
            lines.append("")
            lines.append("📊 Бонуси:")
            lines.extend(bonus_lines)

        if refine_level:
            lines.append("")
            lines.append(f"✨ Заточка: +{refine_level}")

        if not damage_lines and not defense_lines and not bonus_lines:
            lines.append("")
            lines.append("ℹ️ Детальні характеристики для цього лота не знайдені у snapshot.")
            lines.append("Нові лоти зберігатимуть більше інформації після актуальних патчів.")

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
        raise SystemExit("❌ Не знайдено systems/auction_house_system.py. Спочатку потрібні патчі 8.0.1-8.0.5c.")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ Патч 8.0.5d вже застосовано. Змін не потрібно.")
        py_compile.compile(str(target), doraise=True)
        return

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + APPEND_CODE + "\n", encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_8_0_5d_auction_lot_details_inventory_style.\n"
            "systems/auction_house_system.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.5d Auction lot details inventory style застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ systems/auction_house_system.py пройшов py_compile.")
    print("\nЩо змінено:")
    print("- картка лота тепер ближча до відображення предмета в інвентарі")
    print("- INT/STR/DEX/WIS/STA замінено на українські назви")
    print("- приклад: 🔮 Інтелект +9")
    print("- додано формат: 🧰 Тип, 🎯 Слот, 👥 Підходить класам, 🏷 Рівень предмета")
    print("- прибрано player-specific речі: 'Твій рівень' і 'можна буде вдягнути з ...' не показуються")
    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
