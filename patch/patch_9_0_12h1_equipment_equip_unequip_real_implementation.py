from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_12h1_equipment_equip_unequip_real_implementation"


def backup(root, path):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = str(path.relative_to(root)).replace("\\", "_").replace("/", "_")
    out = backup_dir / f"{safe}_{PATCH_NAME}_{stamp}.bak"
    out.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return out


def write_smoke_test(root):
    target = root / "tools" / "smoke_test_equipment_write_contracts.py"
    target.parent.mkdir(exist_ok=True)
    content = '''from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db

USER_ID = 243129101

slots = db.conn.execute(
    "SELECT slot_key, inventory_id FROM equipment_slots WHERE user_id=? ORDER BY slot_key",
    (USER_ID,),
).fetchall()

if len(slots) != 10:
    raise AssertionError(f"Expected 10 equipment slots, got {len(slots)}")

for slot_key, inventory_id in slots:
    if inventory_id is None:
        continue
    owner = db.conn.execute(
        "SELECT user_id FROM inventory WHERE id=?", (int(inventory_id),)
    ).fetchone()
    if not owner or int(owner[0]) != USER_ID:
        raise AssertionError(f"Invalid equipped inventory ownership: {slot_key}={inventory_id}")

from systems import equipment_system as equipment

for name in (
    "equip_inventory_item",
    "unequip_inventory_item",
    "unequip_incompatible_items_after_class_change",
):
    func = getattr(equipment, name, None)
    if not callable(func):
        raise AssertionError(f"Missing callable: {name}")

print("[OK] equipment write runtime contracts")
print("- equipment slots:", len(slots))
print("- equipped:", sum(1 for _, value in slots if value is not None))
print("- direct write functions: available")
'''
    target.write_text(content, encoding="utf-8")
    return target


def main():
    root = Path(__file__).resolve().parents[1]
    equipment_path = root / "systems" / "equipment_system.py"
    db_path = root / "db.py"

    if not equipment_path.exists() or not db_path.exists():
        raise SystemExit("❌ Не знайдено systems/equipment_system.py або db.py.")

    original = equipment_path.read_text(encoding="utf-8")
    marker = "# ✅ ROM 9.0.12h1 EQUIPMENT EQUIP UNEQUIP REAL IMPLEMENTATION"
    if marker in original:
        print("ℹ️ Патч 9.0.12h1 уже застосовано.")
        return

    backup_path = backup(root, equipment_path)

    block = r'''

# ==============================
# ✅ ROM 9.0.12h1 EQUIPMENT EQUIP UNEQUIP REAL IMPLEMENTATION
# ==============================

_EQUIPMENT_WRITE_SLOT_ORDER_V5 = (
    "main_hand", "off_hand", "helmet", "shoulders", "chest",
    "gloves", "legs", "boots", "necklace", "ring",
)

_EQUIPMENT_WRITE_SLOT_LABELS_V5 = {
    "main_hand": "🗡️ Зброя",
    "off_hand": "🛡️ Друга рука",
    "helmet": "🪖 Голова",
    "shoulders": "🦾 Плечі",
    "chest": "🥋 Тіло",
    "gloves": "🧤 Руки",
    "legs": "👖 Ноги",
    "boots": "👟 Взуття",
    "necklace": "📿 Шия",
    "ring": "💍 Кільце",
}

_EQUIPMENT_WRITE_ARMOR_LABELS_V5 = {
    "cloth": "Тканина",
    "leather": "Шкіра",
    "chain": "Кольчуга",
    "plate": "Лати",
}


def _equipment_write_db_v5():
    import db as _db_module
    return _db_module


def _equipment_write_sync_hp_v5(user_id):
    db = _equipment_write_db_v5()
    sync = getattr(db, "sync_user_max_hp", None)
    if callable(sync):
        try:
            return sync(int(user_id), heal_to_full=False)
        except TypeError:
            return sync(int(user_id))
        except Exception:
            return None
    return None


def _equipment_write_ensure_slots_v5(user_id):
    db = _equipment_write_db_v5()
    uid = int(user_id)
    db.conn.execute(
        "CREATE TABLE IF NOT EXISTS equipment_slots ("
        "user_id INTEGER NOT NULL, slot_key TEXT NOT NULL, inventory_id INTEGER, "
        "PRIMARY KEY (user_id, slot_key))"
    )
    for slot_key in _EQUIPMENT_WRITE_SLOT_ORDER_V5:
        db.conn.execute(
            "INSERT OR IGNORE INTO equipment_slots (user_id, slot_key, inventory_id) "
            "VALUES (?, ?, NULL)",
            (uid, slot_key),
        )
    db.conn.commit()


def _equipment_write_get_slot_v5(user_id, slot_key):
    _equipment_write_ensure_slots_v5(user_id)
    db = _equipment_write_db_v5()
    row = db.conn.execute(
        "SELECT inventory_id FROM equipment_slots WHERE user_id=? AND slot_key=?",
        (int(user_id), str(slot_key)),
    ).fetchone()
    return int(row[0]) if row and row[0] is not None else None


def _equipment_write_set_slot_v5(user_id, slot_key, inventory_id):
    _equipment_write_ensure_slots_v5(user_id)
    db = _equipment_write_db_v5()
    db.conn.execute(
        "UPDATE equipment_slots SET inventory_id=? WHERE user_id=? AND slot_key=?",
        (int(inventory_id) if inventory_id is not None else None, int(user_id), str(slot_key)),
    )
    db.conn.commit()


def _equipment_write_find_slot_v5(user_id, inventory_id):
    _equipment_write_ensure_slots_v5(user_id)
    db = _equipment_write_db_v5()
    row = db.conn.execute(
        "SELECT slot_key FROM equipment_slots WHERE user_id=? AND inventory_id=? LIMIT 1",
        (int(user_id), int(inventory_id)),
    ).fetchone()
    return str(row[0]) if row else None


def _equipment_write_item_v5(user_id, inventory_id):
    db = _equipment_write_db_v5()
    row = db.conn.execute(
        "SELECT inv.id, inv.user_id, inv.item_id, COALESCE(inv.durability,100), "
        "COALESCE(inv.refine_level,0), it.name, it.category, it.slot_key, "
        "COALESCE(it.weapon_hands,1), COALESCE(it.item_level,1), "
        "COALESCE(it.item_subtype,''), COALESCE(it.armor_type,'') "
        "FROM inventory inv JOIN items it ON it.id=inv.item_id "
        "WHERE inv.id=? AND inv.user_id=?",
        (int(inventory_id), int(user_id)),
    ).fetchone()
    if not row:
        return None
    keys = (
        "inventory_id", "user_id", "item_id", "durability", "refine_level",
        "name", "category", "slot_key", "weapon_hands", "item_level",
        "item_subtype", "armor_type",
    )
    result = dict(zip(keys, row))
    try:
        display = get_inventory_refined_display_name(int(inventory_id), result["name"])
        if display:
            result["name"] = display
    except Exception:
        pass
    return result


def _equipment_write_required_level_v5(inventory_id, fallback=1):
    db = _equipment_write_db_v5()
    row = db.conn.execute(
        "SELECT COALESCE(it.item_level, ?) FROM inventory inv "
        "JOIN items it ON it.id=inv.item_id WHERE inv.id=?",
        (int(fallback), int(inventory_id)),
    ).fetchone()
    try:
        return max(1, int(row[0] if row else fallback))
    except Exception:
        return max(1, int(fallback or 1))


def _equipment_write_player_level_v5(user_id):
    db = _equipment_write_db_v5()
    row = db.conn.execute("SELECT level FROM users WHERE user_id=?", (int(user_id),)).fetchone()
    return max(1, int(row[0] if row else 1))


def _equipment_write_main_hand_two_handed_v5(user_id):
    inventory_id = _equipment_write_get_slot_v5(user_id, "main_hand")
    if not inventory_id:
        return False
    db = _equipment_write_db_v5()
    row = db.conn.execute(
        "SELECT COALESCE(it.weapon_hands,1) FROM inventory inv "
        "JOIN items it ON it.id=inv.item_id WHERE inv.id=?",
        (int(inventory_id),),
    ).fetchone()
    return bool(row and int(row[0] or 1) == 2)


def equip_inventory_item(user_id, inventory_id):
    """Direct SQL equip implementation preserving the historical string contract."""
    uid = int(user_id)
    iid = int(inventory_id)
    item = _equipment_write_item_v5(uid, iid)

    if not item:
        return "❌ Предмет не знайдено"
    if item.get("category") != "equipment":
        return "❌ Цей предмет не можна одягти"

    slot_key = str(item.get("slot_key") or "")
    if not slot_key:
        return "❌ Для цього предмета не вказано слот"
    if slot_key not in _EQUIPMENT_WRITE_SLOT_ORDER_V5:
        return "❌ Невідомий слот екіпірування"

    player_level = _equipment_write_player_level_v5(uid)
    required_level = _equipment_write_required_level_v5(iid, item.get("item_level", 1))
    if player_level < required_level:
        return (
            "🔒 Ти ще не можеш одягти цей предмет.\n\n"
            f"📦 Предмет: {item['name']}\n"
            f"🏷 Потрібний рівень: {required_level}\n"
            f"👤 Твій рівень: {player_level}"
        )

    class_check = can_equip_inventory_item_by_class(uid, iid)
    if isinstance(class_check, dict) and not class_check.get("success"):
        return class_check.get("message", "❌ Цей предмет не підходить твоєму класу.")

    if slot_key == "off_hand" and _equipment_write_main_hand_two_handed_v5(uid):
        return "❌ Неможливо: дворучна зброя блокує другу руку"

    if slot_key == "main_hand" and int(item.get("weapon_hands") or 1) == 2:
        _equipment_write_set_slot_v5(uid, "off_hand", None)

    # One inventory row may occupy only one slot.
    old_slot = _equipment_write_find_slot_v5(uid, iid)
    if old_slot and old_slot != slot_key:
        _equipment_write_set_slot_v5(uid, old_slot, None)

    _equipment_write_set_slot_v5(uid, slot_key, iid)
    _equipment_write_sync_hp_v5(uid)
    return f"✅ Одягнуто: {item['name']}"


def unequip_inventory_item(user_id, inventory_id):
    """Direct SQL unequip implementation preserving the historical string contract."""
    uid = int(user_id)
    iid = int(inventory_id)
    slot_key = _equipment_write_find_slot_v5(uid, iid)
    if not slot_key:
        return "❌ Цей предмет не вдягнений"
    _equipment_write_set_slot_v5(uid, slot_key, None)
    _equipment_write_sync_hp_v5(uid)
    return f"✅ Знято зі слота: {_EQUIPMENT_WRITE_SLOT_LABELS_V5.get(slot_key, slot_key)}"


def _equipment_write_reason_v5(item_info, message=""):
    lowered = str(message or "").lower()
    slot_key = str((item_info or {}).get("slot_key") or "")
    if "дворуч" in lowered:
        return "конфлікт із дворучною зброєю"
    if slot_key in {"helmet", "shoulders", "chest", "gloves", "legs", "boots"}:
        return "броня не підходить класу"
    if slot_key == "main_hand":
        return "зброя не підходить класу"
    if slot_key == "off_hand":
        return "предмет для другої руки не підходить класу"
    return "не підходить новому класу"


def _equipment_write_display_name_v5(item_info, inventory_id):
    name = str((item_info or {}).get("name") or "Невідомий предмет")
    armor_type = str((item_info or {}).get("armor_type") or "")
    slot_key = str((item_info or {}).get("slot_key") or "")
    if slot_key in {"helmet", "shoulders", "chest", "gloves", "legs", "boots"} and armor_type:
        label = _EQUIPMENT_WRITE_ARMOR_LABELS_V5.get(armor_type, armor_type)
        if label and f"[{label}]" not in name:
            marker = " рівня"
            if marker in name:
                index = name.rfind(marker)
                before, after = name[:index], name[index:]
                parts = before.rsplit(" ", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    name = f"{parts[0]} [{label}] {parts[1]}{after}"
                else:
                    name = f"{name} [{label}]"
            else:
                name = f"{name} [{label}]"
    try:
        refined = get_inventory_refined_display_name(int(inventory_id), name)
        if refined:
            name = refined
    except Exception:
        pass
    return name


def unequip_incompatible_items_after_class_change(user_id):
    """Direct slot updates; compatibility rules remain in the read-only domain."""
    uid = int(user_id)
    _equipment_write_ensure_slots_v5(uid)
    db = _equipment_write_db_v5()
    rows = db.conn.execute(
        "SELECT slot_key, inventory_id FROM equipment_slots WHERE user_id=?",
        (uid,),
    ).fetchall()

    removed_items = []
    for slot_key, inventory_id in rows:
        if inventory_id is None:
            continue
        try:
            compatibility = can_equip_inventory_item_by_class(uid, int(inventory_id))
        except Exception:
            continue
        if isinstance(compatibility, dict) and compatibility.get("success"):
            continue
        if not isinstance(compatibility, dict):
            continue

        item_info = None
        classifier = getattr(db, "get_item_classification_by_inventory_id", None)
        if callable(classifier):
            try:
                item_info = classifier(int(inventory_id))
            except Exception:
                item_info = None
        if not isinstance(item_info, dict):
            raw = _equipment_write_item_v5(uid, int(inventory_id)) or {}
            item_info = {
                "name": raw.get("name"),
                "slot_key": raw.get("slot_key"),
                "armor_type": raw.get("armor_type"),
                "item_subtype": raw.get("item_subtype"),
            }

        reason = _equipment_write_reason_v5(item_info, compatibility.get("message", ""))
        display_name = _equipment_write_display_name_v5(item_info, int(inventory_id))
        _equipment_write_set_slot_v5(uid, str(slot_key), None)
        removed_items.append({
            "inventory_id": int(inventory_id),
            "slot_key": str(slot_key),
            "name": f"{display_name} — {reason}",
            "reason": reason,
        })

    _equipment_write_sync_hp_v5(uid)
    return {
        "success": True,
        "removed_items": removed_items,
        "removed_count": len(removed_items),
    }
'''

    equipment_path.write_text(original.rstrip() + block + "\n", encoding="utf-8")
    smoke_path = write_smoke_test(root)

    try:
        py_compile.compile(str(equipment_path), doraise=True)
        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(smoke_path), doraise=True)
    except Exception as exc:
        equipment_path.write_text(original, encoding="utf-8")
        raise SystemExit(f"❌ Помилка компіляції. equipment_system.py відновлено.\n{exc}")

    print("✅ Патч 9.0.12h1 успішно застосовано.")
    print("✅ Вдягання, зняття та auto-unequip тепер виконуються у systems/equipment_system.py.")
    print("✅ Публічні формати повідомлень і синхронізація max HP збережені.")
    print("Резервні копії:")
    print(f"- {backup_path}")
    print("Перевірки:")
    print("python -m py_compile .\\systems\\equipment_system.py")
    print("python -m py_compile .\\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")
    print("python tools/smoke_test_equipment_write_contracts.py")
    print("python tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
