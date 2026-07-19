from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "6_0_1_refine_core"
DB_MARKER = "# ✅ REFINE SYSTEM CORE V1"

REFINE_SYSTEM_CODE = '"""\nRune Magic RPG - Refine System Core v1\n6.0.1: core refine logic without Telegram UI.\n"""\n\nimport random\n\nREFINE_STONE_ITEM_ID = 401\nSUCCESS_RUNE_ITEM_ID = 402\nWEAPON_MAX_REFINE_LEVEL = 10\nARMOR_MAX_REFINE_LEVEL = 6\n\nWEAPON_REFINE_SUCCESS_CHANCES = {0: 100, 1: 100, 2: 100, 3: 80, 4: 70, 5: 60, 6: 50, 7: 40, 8: 30, 9: 20}\nARMOR_REFINE_SUCCESS_CHANCES = {0: 100, 1: 100, 2: 70, 3: 50, 4: 30, 5: 20}\nWEAPON_REFINE_DAMAGE_MULTIPLIERS = {0: 1.00, 1: 1.05, 2: 1.10, 3: 1.15, 4: 1.22, 5: 1.30, 6: 1.40, 7: 1.52, 8: 1.66, 9: 1.82, 10: 2.00}\nARMOR_REFINE_BASE_HP_BONUS_PERCENT = {0: 0.0, 1: 0.5, 2: 1.0, 3: 1.5, 4: 2.0, 5: 3.0, 6: 4.0}\nARMOR_REFINE_RARITY_HP_MULTIPLIERS = {"common": 1.0, "uncommon": 1.1, "rare": 1.2, "epic": 1.3}\nARMOR_SLOT_KEYS = {"helmet", "shoulders", "chest", "gloves", "legs", "boots"}\n\n\ndef normalize_refine_level(level):\n    try:\n        level = int(level)\n    except Exception:\n        level = 0\n    return max(0, level)\n\n\ndef get_item_refine_kind(item_info):\n    if not item_info:\n        return ""\n    category = item_info.get("category", "")\n    slot_key = item_info.get("slot_key", "")\n    type_ = item_info.get("type", "")\n    if category != "equipment":\n        return ""\n    if slot_key == "main_hand" or type_ == "weapon":\n        return "weapon"\n    if slot_key in ARMOR_SLOT_KEYS:\n        return "armor"\n    return ""\n\n\ndef get_refine_max_level(refine_kind):\n    if refine_kind == "weapon":\n        return WEAPON_MAX_REFINE_LEVEL\n    if refine_kind == "armor":\n        return ARMOR_MAX_REFINE_LEVEL\n    return 0\n\n\ndef get_refine_success_chance(refine_kind, current_level):\n    current_level = normalize_refine_level(current_level)\n    if refine_kind == "weapon":\n        return WEAPON_REFINE_SUCCESS_CHANCES.get(current_level, 0)\n    if refine_kind == "armor":\n        return ARMOR_REFINE_SUCCESS_CHANCES.get(current_level, 0)\n    return 0\n\n\ndef get_refine_failure_level(refine_kind, current_level):\n    current_level = normalize_refine_level(current_level)\n    if refine_kind == "weapon":\n        return current_level if current_level <= 3 else max(0, current_level - 1)\n    if refine_kind == "armor":\n        return current_level if current_level <= 2 else max(0, current_level - 1)\n    return current_level\n\n\ndef get_weapon_refine_damage_multiplier(refine_level):\n    refine_level = min(normalize_refine_level(refine_level), WEAPON_MAX_REFINE_LEVEL)\n    return WEAPON_REFINE_DAMAGE_MULTIPLIERS.get(refine_level, 1.00)\n\n\ndef apply_weapon_refine_to_damage(min_damage, max_damage, refine_level):\n    multiplier = get_weapon_refine_damage_multiplier(refine_level)\n    return int(round(int(min_damage or 0) * multiplier)), int(round(int(max_damage or 0) * multiplier))\n\n\ndef get_armor_refine_hp_bonus_percent(refine_level, rarity):\n    refine_level = min(normalize_refine_level(refine_level), ARMOR_MAX_REFINE_LEVEL)\n    rarity = (rarity or "common").strip().lower()\n    base_bonus = ARMOR_REFINE_BASE_HP_BONUS_PERCENT.get(refine_level, 0.0)\n    rarity_multiplier = ARMOR_REFINE_RARITY_HP_MULTIPLIERS.get(rarity, 1.0)\n    return round(base_bonus * rarity_multiplier, 2)\n\n\ndef get_refine_display_suffix(refine_level):\n    refine_level = normalize_refine_level(refine_level)\n    return "" if refine_level <= 0 else f" [+{refine_level}]"\n\n\ndef can_refine_item(item_info):\n    refine_kind = get_item_refine_kind(item_info)\n    if not refine_kind:\n        return {"success": False, "message": "❌ Цей предмет не можна заточити.", "refine_kind": ""}\n    current_level = normalize_refine_level(item_info.get("refine_level", 0))\n    max_level = get_refine_max_level(refine_kind)\n    if current_level >= max_level:\n        return {"success": False, "message": f"✅ Предмет уже має максимальну заточку +{max_level}.", "refine_kind": refine_kind}\n    return {"success": True, "message": "✅ Предмет можна заточити.", "refine_kind": refine_kind, "current_level": current_level, "max_level": max_level}\n\n\ndef roll_refine_success(refine_kind, current_level, use_success_rune=False):\n    if use_success_rune:\n        return {"success": True, "chance": 100, "roll": None}\n    chance = get_refine_success_chance(refine_kind, current_level)\n    roll = random.randint(1, 100)\n    return {"success": roll <= chance, "chance": chance, "roll": roll}\n\n\ndef perform_refine_attempt(user_id, inventory_id, use_success_rune=False):\n    from db import init_refine_system, get_inventory_item_refine_info, count_user_item, consume_user_item_by_item_id, set_inventory_refine_level\n    init_refine_system()\n    item_info = get_inventory_item_refine_info(inventory_id)\n    if not item_info:\n        return {"success": False, "message": "❌ Предмет не знайдено."}\n    if int(item_info.get("user_id", 0)) != int(user_id):\n        return {"success": False, "message": "❌ Це не твій предмет."}\n    refine_check = can_refine_item(item_info)\n    if not refine_check.get("success"):\n        return refine_check\n    if count_user_item(user_id, REFINE_STONE_ITEM_ID) <= 0:\n        return {"success": False, "message": "❌ Потрібен 🪨 Камінь Посилення."}\n    if use_success_rune and count_user_item(user_id, SUCCESS_RUNE_ITEM_ID) <= 0:\n        return {"success": False, "message": "❌ Потрібна 💎 Руна Успіху."}\n    consume_user_item_by_item_id(user_id, REFINE_STONE_ITEM_ID, 1)\n    if use_success_rune:\n        consume_user_item_by_item_id(user_id, SUCCESS_RUNE_ITEM_ID, 1)\n    refine_kind = refine_check["refine_kind"]\n    current_level = refine_check["current_level"]\n    roll_result = roll_refine_success(refine_kind, current_level, use_success_rune)\n    if roll_result["success"]:\n        new_level = current_level + 1\n        set_inventory_refine_level(inventory_id, new_level)\n        return {"success": True, "refine_success": True, "refine_kind": refine_kind, "old_level": current_level, "new_level": new_level, "chance": roll_result["chance"], "roll": roll_result["roll"], "used_success_rune": bool(use_success_rune), "message": f"✅ Заточка успішна: +{current_level} → +{new_level}"}\n    new_level = get_refine_failure_level(refine_kind, current_level)\n    set_inventory_refine_level(inventory_id, new_level)\n    if new_level < current_level:\n        message = f"❌ Заточка не вдалася: +{current_level} → +{new_level}"\n    else:\n        message = f"❌ Заточка не вдалася: +{current_level} без змін"\n    return {"success": True, "refine_success": False, "refine_kind": refine_kind, "old_level": current_level, "new_level": new_level, "chance": roll_result["chance"], "roll": roll_result["roll"], "used_success_rune": bool(use_success_rune), "message": message}\n'
DB_APPEND_CODE = '\n# ==============================\n# ✅ REFINE SYSTEM CORE V1\n# ==============================\n\nREFINE_STONE_ITEM_ID = 401\nSUCCESS_RUNE_ITEM_ID = 402\n\n\ndef init_refine_system():\n    """Ініціалізує БД для системи заточки."""\n    try:\n        cursor.execute("""\n        ALTER TABLE inventory\n        ADD COLUMN refine_level INTEGER DEFAULT 0\n        """)\n        conn.commit()\n    except Exception:\n        pass\n    seed_refine_items()\n\n\ndef _get_table_columns(table_name):\n    cursor.execute(f"PRAGMA table_info({table_name})")\n    return [row[1] for row in cursor.fetchall()]\n\n\ndef _insert_item_dynamic(values_by_column):\n    columns = _get_table_columns("items")\n    insert_columns = []\n    insert_values = []\n    for column in columns:\n        if column in values_by_column:\n            insert_columns.append(column)\n            insert_values.append(values_by_column[column])\n    placeholders = ", ".join(["?"] * len(insert_columns))\n    columns_sql = ", ".join(insert_columns)\n    cursor.execute(f"""\n    INSERT OR IGNORE INTO items ({columns_sql})\n    VALUES ({placeholders})\n    """, insert_values)\n\n\ndef seed_refine_items():\n    common_values = {\n        "slot_key": "", "weapon_hands": 1, "max_stack": 999, "bonus_str": 0,\n        "bonus_dex": 0, "bonus_int": 0, "bonus_wis": 0, "bonus_sta": 0,\n        "pdef": 0, "mdef": 0, "item_level": 1, "is_generated": 0,\n        "item_subtype": "", "armor_type": "", "weapon_min_damage": 0,\n        "weapon_max_damage": 0, "weapon_min_magic_damage": 0,\n        "weapon_max_magic_damage": 0, "weapon_attack_type": "",\n        "shop_preview_owner": None, "shop_preview_price": 0,\n    }\n    stone_values = dict(common_values)\n    stone_values.update({"id": REFINE_STONE_ITEM_ID, "name": "🪨 Камінь Посилення", "type": "refine_stone", "rarity": "common", "category": "material", "sell_price": 1.0})\n    rune_values = dict(common_values)\n    rune_values.update({"id": SUCCESS_RUNE_ITEM_ID, "name": "💎 Руна Успіху", "type": "success_rune", "rarity": "rare", "category": "material", "sell_price": 5.0})\n    _insert_item_dynamic(stone_values)\n    _insert_item_dynamic(rune_values)\n    conn.commit()\n\n\ndef get_inventory_item_refine_info(inventory_id):\n    init_refine_system()\n    cursor.execute("""\n    SELECT inventory.id, inventory.user_id, inventory.item_id, inventory.quantity,\n           inventory.durability, inventory.refine_level, items.name, items.type,\n           items.rarity, items.category, items.slot_key, items.weapon_hands,\n           items.item_level, items.item_subtype, items.armor_type,\n           items.weapon_min_damage, items.weapon_max_damage,\n           items.weapon_min_magic_damage, items.weapon_max_magic_damage,\n           items.weapon_attack_type\n    FROM inventory\n    JOIN items ON inventory.item_id = items.id\n    WHERE inventory.id=?\n    """, (inventory_id,))\n    row = cursor.fetchone()\n    if not row:\n        return None\n    return {\n        "inventory_id": row[0], "user_id": row[1], "item_id": row[2],\n        "quantity": row[3], "durability": row[4], "refine_level": row[5],\n        "name": row[6], "type": row[7], "rarity": row[8], "category": row[9],\n        "slot_key": row[10], "weapon_hands": row[11], "item_level": row[12],\n        "item_subtype": row[13], "armor_type": row[14],\n        "weapon_min_damage": row[15], "weapon_max_damage": row[16],\n        "weapon_min_magic_damage": row[17], "weapon_max_magic_damage": row[18],\n        "weapon_attack_type": row[19],\n    }\n\n\ndef get_inventory_refine_level(inventory_id):\n    init_refine_system()\n    cursor.execute("SELECT refine_level FROM inventory WHERE id=?", (inventory_id,))\n    row = cursor.fetchone()\n    if not row:\n        return 0\n    try:\n        return int(row[0] or 0)\n    except Exception:\n        return 0\n\n\ndef set_inventory_refine_level(inventory_id, refine_level):\n    init_refine_system()\n    try:\n        refine_level = int(refine_level)\n    except Exception:\n        refine_level = 0\n    refine_level = max(0, refine_level)\n    cursor.execute("UPDATE inventory SET refine_level=? WHERE id=?", (refine_level, inventory_id))\n    conn.commit()\n    return refine_level\n\n\ndef count_user_item(user_id, item_id):\n    cursor.execute("SELECT COALESCE(SUM(quantity), 0) FROM inventory WHERE user_id=? AND item_id=?", (user_id, item_id))\n    row = cursor.fetchone()\n    try:\n        return int((row[0] if row else 0) or 0)\n    except Exception:\n        return 0\n\n\ndef consume_user_item_by_item_id(user_id, item_id, quantity=1):\n    try:\n        quantity = int(quantity)\n    except Exception:\n        quantity = 1\n    if quantity <= 0:\n        return True\n    if count_user_item(user_id, item_id) < quantity:\n        return False\n    remaining = quantity\n    cursor.execute("SELECT id, quantity FROM inventory WHERE user_id=? AND item_id=? ORDER BY id ASC", (user_id, item_id))\n    rows = cursor.fetchall()\n    for inventory_id, stack_quantity in rows:\n        if remaining <= 0:\n            break\n        stack_quantity = int(stack_quantity or 0)\n        take = min(stack_quantity, remaining)\n        new_quantity = stack_quantity - take\n        if new_quantity <= 0:\n            cursor.execute("DELETE FROM inventory WHERE id=?", (inventory_id,))\n        else:\n            cursor.execute("UPDATE inventory SET quantity=? WHERE id=?", (new_quantity, inventory_id))\n        remaining -= take\n    conn.commit()\n    return remaining <= 0\n\n\ndef get_refine_resource_counts(user_id):\n    return {"stone": count_user_item(user_id, REFINE_STONE_ITEM_ID), "success_rune": count_user_item(user_id, SUCCESS_RUNE_ITEM_ID)}\n'


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def write_refine_system(root):
    systems_dir = root / "systems"
    systems_dir.mkdir(exist_ok=True)
    target = systems_dir / "refine_system.py"
    backup_path = make_backup(root, target) if target.exists() else None
    target.write_text(REFINE_SYSTEM_CODE.strip() + "\n", encoding="utf-8")
    return target, backup_path


def patch_db(root):
    target = root / "db.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py. Запускай патч з кореня ROM або з ROM\\patch.")
    text = target.read_text(encoding="utf-8")
    if DB_MARKER in text:
        print("ℹ️ db.py: refine core block уже існує, пропускаю додавання.")
        return target, None
    backup_path = make_backup(root, target)
    target.write_text(text.rstrip() + "\n" + DB_APPEND_CODE + "\n", encoding="utf-8")
    return target, backup_path


def main():
    root = Path(__file__).resolve().parents[1]
    db_path = root / "db.py"
    refine_path = root / "systems" / "refine_system.py"
    db_original = db_path.read_text(encoding="utf-8") if db_path.exists() else ""
    refine_original = refine_path.read_text(encoding="utf-8") if refine_path.exists() else None
    backups = []
    try:
        refine_file, refine_backup = write_refine_system(root)
        if refine_backup:
            backups.append(refine_backup)
        db_file, db_backup = patch_db(root)
        if db_backup:
            backups.append(db_backup)
        py_compile.compile(str(refine_file), doraise=True)
        py_compile.compile(str(db_file), doraise=True)
    except Exception as error:
        if db_original:
            db_path.write_text(db_original, encoding="utf-8")
        if refine_original is not None:
            refine_path.write_text(refine_original, encoding="utf-8")
        elif refine_path.exists():
            try:
                refine_path.unlink()
            except Exception:
                pass
        raise SystemExit("❌ Помилка під час patch_6_0_1_refine_core. Зміни відкотились.\n\n" + str(error))
    print("✅ Патч 6.0.1 Refine Core застосовано успішно.")
    print("✅ Створено / оновлено: systems/refine_system.py")
    print("✅ Оновлено: db.py")
    if backups:
        print("Backup:")
        for backup in backups:
            print(f"- {backup}")
    print("Додано:")
    print("- inventory.refine_level INTEGER DEFAULT 0")
    print("- 🪨 Камінь Посилення, item_id=401")
    print("- 💎 Руна Успіху, item_id=402")
    print("- helper-и db.py для refine")
    print("- ядро системи заточки у systems/refine_system.py")
    print("Наступний етап: 6.0.2 — підключити refine до weapon damage і HP% броні.")


if __name__ == "__main__":
    main()
