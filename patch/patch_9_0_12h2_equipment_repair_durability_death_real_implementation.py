from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_12h2_equipment_repair_durability_death_real_implementation"
TARGET = Path("systems") / "equipment_system.py"
SMOKE = Path("tools") / "smoke_test_equipment_durability_contracts.py"
MARKER = "# ✅ 9.0.12h2 EQUIPMENT REPAIR / DURABILITY / DEATH REAL IMPLEMENTATION"


def backup(root: Path, target: Path) -> Path:
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    out = backup_dir / f"{safe}_{PATCH_NAME}_{stamp}.bak"
    out.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return out


IMPLEMENTATION = r'''

# ==============================
# ✅ 9.0.12h2 EQUIPMENT REPAIR / DURABILITY / DEATH REAL IMPLEMENTATION
# ==============================

_REPAIR_MULTIPLIERS_9_0_12H2 = {
    "common": 1.0,
    "uncommon": 2.5,
    "rare": 7.0,
    "epic": 18.0,
}


def _equipment_db_9_0_12h2():
    import db
    return db


def _equipment_sync_hp_9_0_12h2(user_id):
    try:
        db = _equipment_db_9_0_12h2()
        sync = getattr(db, "sync_user_max_hp", None)
        if callable(sync):
            sync(int(user_id), heal_to_full=False)
    except Exception:
        pass


def _equipment_display_name_9_0_12h2(inventory_id, base_name):
    try:
        func = globals().get("get_inventory_refined_display_name")
        if callable(func):
            value = func(int(inventory_id))
            if value:
                return str(value)
    except Exception:
        pass
    return str(base_name or "Предмет")


def get_rarity_repair_multiplier(rarity):
    return float(_REPAIR_MULTIPLIERS_9_0_12H2.get(str(rarity or "common").lower(), 1.0))


def calculate_repair_cost(durability, rarity):
    try:
        durability = int(100 if durability is None else durability)
    except Exception:
        durability = 100
    durability = max(0, min(100, durability))
    if durability >= 100:
        return 0.0
    return round((100 - durability) * get_rarity_repair_multiplier(rarity) * 0.05, 2)


def _equipment_slot_rows_9_0_12h2(user_id):
    db = _equipment_db_9_0_12h2()
    db.conn.row_factory = __import__("sqlite3").Row
    return db.conn.execute(
        """
        SELECT es.slot_key,
               es.inventory_id,
               inv.item_id,
               inv.durability,
               COALESCE(inv.refine_level, 0) AS refine_level,
               i.name,
               i.rarity
        FROM equipment_slots es
        LEFT JOIN inventory inv
          ON inv.id = es.inventory_id
         AND inv.user_id = es.user_id
        LEFT JOIN items i
          ON i.id = inv.item_id
        WHERE es.user_id=?
        ORDER BY CASE es.slot_key
            WHEN 'main_hand' THEN 1
            WHEN 'off_hand' THEN 2
            WHEN 'helmet' THEN 3
            WHEN 'shoulders' THEN 4
            WHEN 'chest' THEN 5
            WHEN 'gloves' THEN 6
            WHEN 'legs' THEN 7
            WHEN 'boots' THEN 8
            WHEN 'necklace' THEN 9
            WHEN 'ring' THEN 10
            ELSE 99 END
        """,
        (int(user_id),),
    ).fetchall()


_SLOT_NAMES_9_0_12H2 = {
    "main_hand": "Основна рука",
    "off_hand": "Друга рука",
    "helmet": "Шолом",
    "shoulders": "Наплічники",
    "chest": "Обладунок",
    "gloves": "Рукавиці",
    "legs": "Поножі",
    "boots": "Чоботи",
    "necklace": "Намисто",
    "ring": "Перстень",
}


def get_equipped_items_for_repair(user_id):
    result = []
    for row in _equipment_slot_rows_9_0_12h2(user_id):
        slot_key = row["slot_key"]
        inventory_id = row["inventory_id"]
        slot_name = _SLOT_NAMES_9_0_12H2.get(slot_key, slot_key)

        if not inventory_id:
            result.append({
                "slot": slot_name,
                "slot_name": slot_name,
                "slot_key": slot_key,
                "inventory_id": None,
                "name": "Порожньо",
                "rarity": None,
                "durability": None,
                "repair_cost": 0.0,
                "is_broken": False,
                "refine_level": 0,
            })
            continue

        durability = 100 if row["durability"] is None else max(0, min(100, int(row["durability"])))
        rarity = str(row["rarity"] or "common")
        name = _equipment_display_name_9_0_12h2(inventory_id, row["name"])
        result.append({
            "slot": slot_name,
            "slot_name": slot_name,
            "slot_key": slot_key,
            "inventory_id": int(inventory_id),
            "item_id": int(row["item_id"]),
            "name": name,
            "rarity": rarity,
            "durability": durability,
            "repair_cost": calculate_repair_cost(durability, rarity),
            "is_broken": durability <= 0,
            "refine_level": int(row["refine_level"] or 0),
        })
    return result


def get_total_repair_cost(user_id):
    return round(sum(float(x.get("repair_cost", 0.0) or 0.0) for x in get_equipped_items_for_repair(user_id)), 2)


def _equipment_wallet_9_0_12h2(db, user_id):
    row = db.conn.execute("SELECT gold FROM users WHERE user_id=?", (int(user_id),)).fetchone()
    return float(row[0] or 0.0) if row else 0.0


def repair_equipped_item(user_id, inventory_id):
    db = _equipment_db_9_0_12h2()
    user_id = int(user_id)
    inventory_id = int(inventory_id)
    row = db.conn.execute(
        """
        SELECT inv.durability, COALESCE(inv.refine_level, 0), i.name, i.rarity
        FROM equipment_slots es
        JOIN inventory inv ON inv.id=es.inventory_id AND inv.user_id=es.user_id
        JOIN items i ON i.id=inv.item_id
        WHERE es.user_id=? AND es.inventory_id=?
        LIMIT 1
        """,
        (user_id, inventory_id),
    ).fetchone()
    if not row:
        return {"success": False, "message": "❌ Цей предмет не вдягнений або не належить персонажу."}

    old_durability = 100 if row[0] is None else max(0, min(100, int(row[0])))
    name = _equipment_display_name_9_0_12h2(inventory_id, row[2])
    rarity = str(row[3] or "common")
    cost = calculate_repair_cost(old_durability, rarity)
    if old_durability >= 100 or cost <= 0:
        return {"success": False, "message": f"ℹ️ {name} уже має максимальну міцність.", "inventory_id": inventory_id}

    try:
        db.conn.execute("BEGIN IMMEDIATE")
        wallet = _equipment_wallet_9_0_12h2(db, user_id)
        if wallet + 1e-9 < cost:
            db.conn.rollback()
            return {"success": False, "message": f"❌ Недостатньо золота. Потрібно: {cost:.2f} 💰"}
        db.conn.execute("UPDATE users SET gold=gold-? WHERE user_id=?", (cost, user_id))
        db.conn.execute("UPDATE inventory SET durability=100 WHERE id=? AND user_id=?", (inventory_id, user_id))
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise

    _equipment_sync_hp_9_0_12h2(user_id)
    message = (
        "✅ Предмет відремонтовано.\n\n"
        f"📦 {name}\n"
        f"🛠️ Міцність: {old_durability}/100 → 100/100\n"
        f"💳 Сплачено: {cost:.2f} 💰 золото"
    )
    return {
        "success": True,
        "message": message,
        "inventory_id": inventory_id,
        "name": name,
        "old_durability": old_durability,
        "new_durability": 100,
        "cost": cost,
    }


def repair_inventory_item(user_id, inventory_id):
    return repair_equipped_item(user_id, inventory_id)


def repair_all_equipped(user_id):
    db = _equipment_db_9_0_12h2()
    user_id = int(user_id)
    items = [x for x in get_equipped_items_for_repair(user_id) if x.get("inventory_id") and int(x.get("durability") or 0) < 100]
    if not items:
        return {"success": False, "message": "ℹ️ Усе вдягнене спорядження вже відремонтоване."}
    total = round(sum(float(x["repair_cost"]) for x in items), 2)
    try:
        db.conn.execute("BEGIN IMMEDIATE")
        wallet = _equipment_wallet_9_0_12h2(db, user_id)
        if wallet + 1e-9 < total:
            db.conn.rollback()
            return {"success": False, "message": f"❌ Недостатньо золота. Потрібно: {total:.2f} 💰"}
        db.conn.execute("UPDATE users SET gold=gold-? WHERE user_id=?", (total, user_id))
        db.conn.executemany(
            "UPDATE inventory SET durability=100 WHERE id=? AND user_id=?",
            [(int(x["inventory_id"]), user_id) for x in items],
        )
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    _equipment_sync_hp_9_0_12h2(user_id)
    return {
        "success": True,
        "message": (
            "✅ Усе спорядження відремонтовано.\n\n"
            f"📦 Відремонтовано предметів: {len(items)}\n"
            f"💳 Сплачено: {total:.2f} 💰 золото"
        ),
        "count": len(items),
        "cost": total,
        "items": items,
    }


def set_inventory_item_durability(inventory_id, durability, user_id=None):
    db = _equipment_db_9_0_12h2()
    inventory_id = int(inventory_id)
    durability = max(0, min(100, int(durability)))
    if user_id is None:
        owner = db.conn.execute("SELECT user_id FROM inventory WHERE id=?", (inventory_id,)).fetchone()
        if not owner:
            return {"success": False, "message": "❌ Предмет не знайдено."}
        user_id = int(owner[0])
    cur = db.conn.execute(
        "UPDATE inventory SET durability=? WHERE id=? AND user_id=?",
        (durability, inventory_id, int(user_id)),
    )
    db.conn.commit()
    _equipment_sync_hp_9_0_12h2(user_id)
    return {"success": cur.rowcount > 0, "inventory_id": inventory_id, "durability": durability}


def damage_equipped_items(user_id, amount=1):
    db = _equipment_db_9_0_12h2()
    user_id = int(user_id)
    amount = max(0, int(amount or 0))
    if amount <= 0:
        return {"success": True, "damaged": 0, "amount": 0, "items": []}
    rows = db.conn.execute(
        """
        SELECT inv.id, COALESCE(inv.durability, 100), i.name
        FROM equipment_slots es
        JOIN inventory inv ON inv.id=es.inventory_id AND inv.user_id=es.user_id
        JOIN items i ON i.id=inv.item_id
        WHERE es.user_id=? AND es.inventory_id IS NOT NULL
        """,
        (user_id,),
    ).fetchall()
    changed = []
    try:
        db.conn.execute("BEGIN IMMEDIATE")
        for inv_id, old_value, base_name in rows:
            old_value = max(0, min(100, int(old_value or 0)))
            new_value = max(0, old_value - amount)
            if new_value == old_value:
                continue
            db.conn.execute("UPDATE inventory SET durability=? WHERE id=? AND user_id=?", (new_value, int(inv_id), user_id))
            changed.append({
                "inventory_id": int(inv_id),
                "name": _equipment_display_name_9_0_12h2(inv_id, base_name),
                "old_durability": old_value,
                "new_durability": new_value,
                "is_broken": new_value <= 0,
            })
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    _equipment_sync_hp_9_0_12h2(user_id)
    return {"success": True, "damaged": len(changed), "amount": amount, "items": changed}


def damage_equipped_items_on_death(user_id, amount=5):
    return damage_equipped_items(user_id, amount=5)


def reduce_equipped_item_durability(user_id, inventory_id, amount=1):
    db = _equipment_db_9_0_12h2()
    row = db.conn.execute(
        """
        SELECT COALESCE(inv.durability,100)
        FROM equipment_slots es
        JOIN inventory inv ON inv.id=es.inventory_id AND inv.user_id=es.user_id
        WHERE es.user_id=? AND es.inventory_id=?
        """,
        (int(user_id), int(inventory_id)),
    ).fetchone()
    if not row:
        return {"success": False, "message": "❌ Вдягнений предмет не знайдено."}
    old_value = max(0, min(100, int(row[0] or 0)))
    new_value = max(0, old_value - max(0, int(amount or 0)))
    result = set_inventory_item_durability(inventory_id, new_value, user_id=user_id)
    result.update({"old_durability": old_value, "new_durability": new_value, "is_broken": new_value <= 0})
    return result


def apply_equipment_wear(user_id, amount=1):
    return damage_equipped_items(user_id, amount=amount)


def apply_equipment_wear_after_combat(user_id, amount=1):
    return damage_equipped_items(user_id, amount=amount)


def apply_random_durability_wear_on_victory(user_id, chance=None, amount=1):
    """Зберігає старий принцип: за успішного roll зношується один випадковий вдягнений предмет."""
    import random
    db = _equipment_db_9_0_12h2()
    if chance is None:
        chance = float(getattr(db, "DURABILITY_WEAR_CHANCE", 0.25))
    chance = max(0.0, min(1.0, float(chance)))
    if random.random() >= chance:
        return {"success": True, "worn": False, "damaged": 0, "items": []}
    rows = db.conn.execute(
        """
        SELECT inv.id
        FROM equipment_slots es
        JOIN inventory inv ON inv.id=es.inventory_id AND inv.user_id=es.user_id
        WHERE es.user_id=? AND es.inventory_id IS NOT NULL AND COALESCE(inv.durability,100)>0
        """,
        (int(user_id),),
    ).fetchall()
    if not rows:
        return {"success": True, "worn": False, "damaged": 0, "items": []}
    inventory_id = int(random.choice(rows)[0])
    result = reduce_equipped_item_durability(user_id, inventory_id, amount=amount)
    return {"success": bool(result.get("success")), "worn": True, "damaged": 1, "items": [result], "inventory_id": inventory_id}


def roll_equipment_wear_after_combat(user_id, chance=None, amount=1):
    return apply_random_durability_wear_on_victory(user_id, chance=chance, amount=amount)
'''


SMOKE_CODE = r'''from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db

USER_ID = 243129101

rows = db.get_equipped_items_for_repair(USER_ID)
assert isinstance(rows, list)
assert len(rows) == 10
for row in rows:
    assert isinstance(row, dict)
    for key in ("slot_key", "slot", "inventory_id", "repair_cost", "is_broken"):
        assert key in row, (key, row)
    if row["inventory_id"]:
        assert isinstance(row["durability"], int)
        assert 0 <= row["durability"] <= 100
        assert isinstance(row["repair_cost"], (int, float))

calc = db.calculate_repair_cost(95, "common")
assert abs(float(calc) - 0.25) < 1e-9, calc
assert abs(float(db.calculate_repair_cost(95, "uncommon")) - 0.62) < 1e-9
assert abs(float(db.calculate_repair_cost(95, "rare")) - 1.75) < 1e-9
assert abs(float(db.calculate_repair_cost(95, "epic")) - 4.5) < 1e-9

total = db.get_total_repair_cost(USER_ID)
assert isinstance(total, (int, float))

for name in (
    "repair_equipped_item",
    "repair_all_equipped",
    "damage_equipped_items_on_death",
    "apply_random_durability_wear_on_victory",
):
    assert callable(getattr(db, name, None)), name

print("[OK] equipment repair/durability runtime contracts")
print("- equipment slots:", len(rows))
print("- repairable:", sum(1 for x in rows if x.get("inventory_id") and x.get("durability", 100) < 100))
print("- total repair cost:", total)
print("- death durability loss: 5")
'''


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET
    smoke = root / SMOKE
    if not target.exists():
        raise SystemExit(f"❌ Не знайдено файл: {target}")

    original = target.read_text(encoding="utf-8")
    if MARKER in original:
        print("ℹ️ Патч 9.0.12h2 уже застосовано.")
        return

    backups = [backup(root, target)]
    if smoke.exists():
        backups.append(backup(root, smoke))

    target.write_text(original.rstrip() + "\n" + IMPLEMENTATION + "\n", encoding="utf-8")
    smoke.parent.mkdir(exist_ok=True)
    smoke.write_text(SMOKE_CODE, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
        py_compile.compile(str(smoke), doraise=True)
    except Exception as exc:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(f"❌ Помилка компіляції після патча. equipment_system.py відновлено.\n{exc}")

    print("✅ Патч 9.0.12h2 успішно застосовано.")
    print("✅ Ремонт, міцність і втрата міцності після смерті тепер виконуються у systems/equipment_system.py.")
    print("✅ Правило смерті −5 міцності та чинна формула ремонту збережені.")
    print("Резервні копії:")
    for item in backups:
        print(f"- {item}")
    print("Перевірки:")
    print("python -m py_compile .\\systems\\equipment_system.py")
    print("python -m py_compile .\\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")
    print("python tools/smoke_test_equipment_durability_contracts.py")
    print("python tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
