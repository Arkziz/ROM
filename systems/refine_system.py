"""
Rune Magic RPG - Refine System Core v1
6.0.1: core refine logic without Telegram UI.
"""

import random

REFINE_STONE_ITEM_ID = 601
SUCCESS_RUNE_ITEM_ID = 602
WEAPON_MAX_REFINE_LEVEL = 10
ARMOR_MAX_REFINE_LEVEL = 6

WEAPON_REFINE_SUCCESS_CHANCES = {0: 100, 1: 100, 2: 100, 3: 80, 4: 70, 5: 60, 6: 50, 7: 40, 8: 30, 9: 20}
ARMOR_REFINE_SUCCESS_CHANCES = {0: 100, 1: 100, 2: 70, 3: 50, 4: 30, 5: 20}
WEAPON_REFINE_DAMAGE_MULTIPLIERS = {0: 1.00, 1: 1.05, 2: 1.10, 3: 1.15, 4: 1.22, 5: 1.30, 6: 1.40, 7: 1.52, 8: 1.66, 9: 1.82, 10: 2.00}
ARMOR_REFINE_BASE_HP_BONUS_PERCENT = {0: 0.0, 1: 0.5, 2: 1.0, 3: 1.5, 4: 2.0, 5: 3.0, 6: 4.0}
ARMOR_REFINE_RARITY_HP_MULTIPLIERS = {"common": 1.0, "uncommon": 1.1, "rare": 1.2, "epic": 1.3}
ARMOR_SLOT_KEYS = {"helmet", "shoulders", "chest", "gloves", "legs", "boots"}


def normalize_refine_level(level):
    try:
        level = int(level)
    except Exception:
        level = 0
    return max(0, level)


def get_item_refine_kind(item_info):
    if not item_info:
        return ""
    category = item_info.get("category", "")
    slot_key = item_info.get("slot_key", "")
    type_ = item_info.get("type", "")
    if category != "equipment":
        return ""
    if slot_key == "main_hand" or type_ == "weapon":
        return "weapon"
    if slot_key in ARMOR_SLOT_KEYS:
        return "armor"
    return ""


def get_refine_max_level(refine_kind):
    if refine_kind == "weapon":
        return WEAPON_MAX_REFINE_LEVEL
    if refine_kind == "armor":
        return ARMOR_MAX_REFINE_LEVEL
    return 0


def get_refine_success_chance(refine_kind, current_level):
    current_level = normalize_refine_level(current_level)
    if refine_kind == "weapon":
        return WEAPON_REFINE_SUCCESS_CHANCES.get(current_level, 0)
    if refine_kind == "armor":
        return ARMOR_REFINE_SUCCESS_CHANCES.get(current_level, 0)
    return 0


def get_refine_failure_level(refine_kind, current_level):
    current_level = normalize_refine_level(current_level)
    if refine_kind == "weapon":
        return current_level if current_level <= 3 else max(0, current_level - 1)
    if refine_kind == "armor":
        return current_level if current_level <= 2 else max(0, current_level - 1)
    return current_level


def get_weapon_refine_damage_multiplier(refine_level):
    refine_level = min(normalize_refine_level(refine_level), WEAPON_MAX_REFINE_LEVEL)
    return WEAPON_REFINE_DAMAGE_MULTIPLIERS.get(refine_level, 1.00)


def apply_weapon_refine_to_damage(min_damage, max_damage, refine_level):
    multiplier = get_weapon_refine_damage_multiplier(refine_level)
    return int(round(int(min_damage or 0) * multiplier)), int(round(int(max_damage or 0) * multiplier))


def get_armor_refine_hp_bonus_percent(refine_level, rarity):
    refine_level = min(normalize_refine_level(refine_level), ARMOR_MAX_REFINE_LEVEL)
    rarity = (rarity or "common").strip().lower()
    base_bonus = ARMOR_REFINE_BASE_HP_BONUS_PERCENT.get(refine_level, 0.0)
    rarity_multiplier = ARMOR_REFINE_RARITY_HP_MULTIPLIERS.get(rarity, 1.0)
    return round(base_bonus * rarity_multiplier, 2)


def get_refine_display_suffix(refine_level):
    refine_level = normalize_refine_level(refine_level)
    return "" if refine_level <= 0 else f" [+{refine_level}]"


def can_refine_item(item_info):
    refine_kind = get_item_refine_kind(item_info)
    if not refine_kind:
        return {"success": False, "message": "❌ Цей предмет не можна заточити.", "refine_kind": ""}
    current_level = normalize_refine_level(item_info.get("refine_level", 0))
    max_level = get_refine_max_level(refine_kind)
    if current_level >= max_level:
        return {"success": False, "message": f"✅ Предмет уже має максимальну заточку +{max_level}.", "refine_kind": refine_kind}
    return {"success": True, "message": "✅ Предмет можна заточити.", "refine_kind": refine_kind, "current_level": current_level, "max_level": max_level}


def roll_refine_success(refine_kind, current_level, use_success_rune=False):
    if use_success_rune:
        return {"success": True, "chance": 100, "roll": None}
    chance = get_refine_success_chance(refine_kind, current_level)
    roll = random.randint(1, 100)
    return {"success": roll <= chance, "chance": chance, "roll": roll}


def perform_refine_attempt(user_id, inventory_id, use_success_rune=False, idempotency_key=None, db_path=None):
    """Atomically consume resources, apply refine result, and persist one attempt."""
    import json
    import sqlite3
    from datetime import datetime, timezone
    from pathlib import Path
    uid = int(user_id)
    inv_id = int(inventory_id)
    use_rune = bool(use_success_rune)
    key = str(idempotency_key or "").strip()
    if not key:
        return {"success": False, "message": "❌ Відсутній ключ операції заточки."}
    path = Path(db_path) if db_path is not None else Path(__file__).resolve().parents[1] / "game.db"
    conn = sqlite3.connect(str(path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        conn.executescript("""CREATE TABLE IF NOT EXISTS refine_attempts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            inventory_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            refine_kind TEXT NOT NULL,
            old_level INTEGER NOT NULL,
            new_level INTEGER NOT NULL,
            success_chance INTEGER NOT NULL,
            roll INTEGER,
            refine_success INTEGER NOT NULL,
            used_success_rune INTEGER NOT NULL,
            stone_quantity INTEGER NOT NULL DEFAULT 1,
            success_rune_quantity INTEGER NOT NULL DEFAULT 0,
            idempotency_key TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT,
            FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE RESTRICT
        );CREATE INDEX IF NOT EXISTS ix_refine_attempts_user ON refine_attempts(user_id,id DESC);""")
        conn.commit()
        conn.execute("BEGIN IMMEDIATE")
        old_attempt = conn.execute("SELECT * FROM refine_attempts WHERE idempotency_key=?", (key,)).fetchone()
        if old_attempt:
            conn.commit()
            row = dict(old_attempt)
            return {"success": True, "idempotent_replay": True, "refine_success": bool(row["refine_success"]), "refine_kind": row["refine_kind"], "old_level": row["old_level"], "new_level": row["new_level"], "chance": row["success_chance"], "roll": row["roll"], "used_success_rune": bool(row["used_success_rune"]), "message": "ℹ️ Цю спробу заточки вже виконано."}
        item = conn.execute("""SELECT inventory.id,inventory.user_id,inventory.item_id,COALESCE(inventory.refine_level,0) refine_level,items.name,items.type,items.category,items.slot_key,items.weapon_hands,items.item_subtype,items.armor_type FROM inventory JOIN items ON items.id=inventory.item_id WHERE inventory.id=?""", (inv_id,)).fetchone()
        if not item:
            conn.rollback(); return {"success": False, "message": "❌ Предмет не знайдено."}
        if int(item["user_id"]) != uid:
            conn.rollback(); return {"success": False, "message": "❌ Це не твій предмет."}
        info = dict(item)
        check = can_refine_item(info)
        if not check.get("success"):
            conn.rollback(); return check
        def total(item_id):
            return int(conn.execute("SELECT COALESCE(SUM(quantity),0) FROM inventory WHERE user_id=? AND item_id=? AND quantity>0", (uid,item_id)).fetchone()[0])
        if total(REFINE_STONE_ITEM_ID) < 1:
            conn.rollback(); return {"success": False, "message": "❌ Потрібен 🪨 Камінь Посилення."}
        if use_rune and total(SUCCESS_RUNE_ITEM_ID) < 1:
            conn.rollback(); return {"success": False, "message": "❌ Потрібна 💎 Руна Успіху."}
        def consume(item_id):
            row = conn.execute("SELECT id,quantity FROM inventory WHERE user_id=? AND item_id=? AND quantity>0 ORDER BY id LIMIT 1", (uid,item_id)).fetchone()
            if not row: raise RuntimeError("resource disappeared during refine")
            if int(row["quantity"]) == 1: conn.execute("DELETE FROM inventory WHERE id=? AND user_id=?", (int(row["id"]),uid))
            else: conn.execute("UPDATE inventory SET quantity=quantity-1 WHERE id=? AND user_id=? AND quantity>1", (int(row["id"]),uid))
        kind = check["refine_kind"]
        current = int(check["current_level"])
        roll_result = roll_refine_success(kind,current,use_rune)
        new_level = current + 1 if roll_result["success"] else get_refine_failure_level(kind,current)
        consume(REFINE_STONE_ITEM_ID)
        if use_rune: consume(SUCCESS_RUNE_ITEM_ID)
        changed = conn.execute("UPDATE inventory SET refine_level=? WHERE id=? AND user_id=? AND COALESCE(refine_level,0)=?", (new_level,inv_id,uid,current)).rowcount
        if changed != 1: raise RuntimeError("refine target changed concurrently")
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("INSERT INTO refine_attempts(user_id,inventory_id,item_id,refine_kind,old_level,new_level,success_chance,roll,refine_success,used_success_rune,stone_quantity,success_rune_quantity,idempotency_key,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (uid,inv_id,int(item["item_id"]),kind,current,new_level,int(roll_result["chance"]),roll_result["roll"],1 if roll_result["success"] else 0,1 if use_rune else 0,1,1 if use_rune else 0,key,now))
        conn.commit()
        if roll_result["success"]: message=f"✅ Заточка успішна: +{current} → +{new_level}"
        elif new_level < current: message=f"❌ Заточка не вдалася: +{current} → +{new_level}"
        else: message=f"❌ Заточка не вдалася: +{current} без змін"
        return {"success": True, "idempotent_replay": False, "refine_success": bool(roll_result["success"]), "refine_kind": kind, "old_level": current, "new_level": new_level, "chance": int(roll_result["chance"]), "roll": roll_result["roll"], "used_success_rune": use_rune, "message": message}
    except Exception as error:
        try: conn.rollback()
        except Exception: pass
        return {"success": False, "message": f"❌ Заточку скасовано без списання ресурсів: {error}"}
    finally:
        conn.close()

