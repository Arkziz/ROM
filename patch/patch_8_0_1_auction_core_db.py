from pathlib import Path
from datetime import datetime
import py_compile
import sys

PATCH_NAME = "8_0_1_auction_core_db"
SYSTEM_PATH = Path("systems") / "auction_house_system.py"
DB_MARKER = "# ✅ AUCTION HOUSE DB WRAPPERS V1"

SYSTEM_CODE = r'''
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_DOWN
import json

from db import conn, cursor


# ==============================
# AUCTION HOUSE CORE CONSTANTS
# ==============================

AUCTION_STATUS_ACTIVE = "ACTIVE"
AUCTION_STATUS_SOLD_UNCLAIMED = "SOLD_UNCLAIMED"
AUCTION_STATUS_SOLD_CLAIMED = "SOLD_CLAIMED"
AUCTION_STATUS_EXPIRED_UNCLAIMED = "EXPIRED_UNCLAIMED"
AUCTION_STATUS_EXPIRED_CLAIMED = "EXPIRED_CLAIMED"
AUCTION_STATUS_DELETED = "DELETED"

AUCTION_ACTIVE_DAYS = 7
AUCTION_CLAIM_DAYS = 30
AUCTION_MAX_ACTIVE_LOTS_PER_USER = 20

AUCTION_MIN_PRICE = Decimal("1.0")
AUCTION_MAX_PRICE = Decimal("999999.0")
AUCTION_PRICE_QUANT = Decimal("0.01")

AUCTION_CATEGORY_EQUIPMENT = "equipment"
AUCTION_CATEGORY_POTION = "potion"
AUCTION_CATEGORY_MATERIAL = "material"

AUCTION_ALLOWED_CATEGORIES = {
    AUCTION_CATEGORY_EQUIPMENT,
    AUCTION_CATEGORY_POTION,
    AUCTION_CATEGORY_MATERIAL,
}

AUCTION_HISTORY_LISTED = "LISTED"
AUCTION_HISTORY_SOLD = "SOLD"
AUCTION_HISTORY_CANCELLED = "CANCELLED"
AUCTION_HISTORY_EXPIRED = "EXPIRED"
AUCTION_HISTORY_ITEM_CLAIMED = "ITEM_CLAIMED"
AUCTION_HISTORY_GOLD_CLAIMED = "GOLD_CLAIMED"
AUCTION_HISTORY_DELETED = "DELETED"


# ==============================
# BASIC HELPERS
# ==============================

def now_iso():
    return datetime.now().isoformat()


def iso_after_days(days):
    return (datetime.now() + timedelta(days=int(days))).isoformat()


def decimal_to_price_text(value):
    """
    Normalize user/input price to DB-safe text.

    The auction house uses Decimal, and stores price as TEXT to avoid binary float issues.
    """

    if isinstance(value, Decimal):
        price = value
    else:
        try:
            price = Decimal(str(value).strip().replace(",", "."))
        except (InvalidOperation, ValueError, AttributeError):
            raise ValueError("Некоректна ціна.")

    price = price.quantize(AUCTION_PRICE_QUANT, rounding=ROUND_DOWN)

    if price < AUCTION_MIN_PRICE:
        raise ValueError(f"Мінімальна ціна: {AUCTION_MIN_PRICE} золота.")

    if price > AUCTION_MAX_PRICE:
        raise ValueError(f"Максимальна ціна: {AUCTION_MAX_PRICE} золота.")

    # Keep a simple human-readable decimal string.
    return format(price, "f")


def validate_auction_price(value):
    try:
        return {
            "success": True,
            "price": decimal_to_price_text(value),
        }
    except ValueError as error:
        return {
            "success": False,
            "message": f"❌ {error}",
        }


def auction_price_to_decimal(value):
    return Decimal(str(value or "0").strip().replace(",", "."))


def normalize_auction_category(category):
    category = str(category or "").strip().lower()

    aliases = {
        "⚔️ спорядження": AUCTION_CATEGORY_EQUIPMENT,
        "спорядження": AUCTION_CATEGORY_EQUIPMENT,
        "equipment": AUCTION_CATEGORY_EQUIPMENT,
        "gear": AUCTION_CATEGORY_EQUIPMENT,
        "🧪 зілля": AUCTION_CATEGORY_POTION,
        "зілля": AUCTION_CATEGORY_POTION,
        "potion": AUCTION_CATEGORY_POTION,
        "potions": AUCTION_CATEGORY_POTION,
        "🪨 матеріали": AUCTION_CATEGORY_MATERIAL,
        "матеріали": AUCTION_CATEGORY_MATERIAL,
        "material": AUCTION_CATEGORY_MATERIAL,
        "materials": AUCTION_CATEGORY_MATERIAL,
    }

    category = aliases.get(category, category)

    if category not in AUCTION_ALLOWED_CATEGORIES:
        raise ValueError("Некоректна категорія Торгового Дому.")

    return category


def safe_json_dumps(value):
    return json.dumps(value or {}, ensure_ascii=False, sort_keys=True)


def safe_json_loads(value):
    try:
        return json.loads(value or "{}")
    except Exception:
        return {}


# ==============================
# INIT DB
# ==============================

def init_auction_house():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auction_lots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        seller_user_id INTEGER NOT NULL,
        buyer_user_id INTEGER,

        item_type TEXT NOT NULL,
        item_source TEXT DEFAULT '',
        item_ref_id INTEGER,
        item_snapshot_json TEXT NOT NULL,

        item_name TEXT NOT NULL,
        item_name_norm TEXT NOT NULL,
        category TEXT NOT NULL,
        rarity TEXT DEFAULT '',
        level INTEGER DEFAULT 0,
        enhancement_level INTEGER DEFAULT 0,
        durability_current INTEGER,
        durability_max INTEGER,
        quantity INTEGER DEFAULT 1,

        price TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE',

        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        sold_at TEXT,
        claimed_at TEXT,
        delete_after TEXT,
        updated_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auction_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_id INTEGER,
        event_type TEXT NOT NULL,
        actor_user_id INTEGER,
        seller_user_id INTEGER,
        buyer_user_id INTEGER,
        item_name TEXT,
        category TEXT,
        quantity INTEGER DEFAULT 1,
        price TEXT,
        status_before TEXT,
        status_after TEXT,
        details_json TEXT DEFAULT '{}',
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_auction_lots_status_created
    ON auction_lots(status, created_at)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_auction_lots_seller_status
    ON auction_lots(seller_user_id, status)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_auction_lots_buyer_status
    ON auction_lots(buyer_user_id, status)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_auction_lots_category_status
    ON auction_lots(category, status)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_auction_lots_name_norm
    ON auction_lots(item_name_norm)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_auction_history_lot
    ON auction_history(lot_id)
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_auction_history_actor
    ON auction_history(actor_user_id, created_at)
    """)

    conn.commit()


# ==============================
# HISTORY
# ==============================

def add_auction_history(
    lot_id=None,
    event_type=AUCTION_HISTORY_LISTED,
    actor_user_id=None,
    seller_user_id=None,
    buyer_user_id=None,
    item_name="",
    category="",
    quantity=1,
    price="",
    status_before=None,
    status_after=None,
    details=None,
):
    init_auction_house()

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
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lot_id,
        event_type,
        actor_user_id,
        seller_user_id,
        buyer_user_id,
        item_name,
        category,
        int(quantity or 1),
        str(price or ""),
        status_before,
        status_after,
        safe_json_dumps(details or {}),
        now_iso(),
    ))

    conn.commit()


# ==============================
# READ HELPERS
# ==============================

def get_auction_lot_by_id(lot_id):
    init_auction_house()
    cursor.execute("SELECT * FROM auction_lots WHERE id=?", (lot_id,))
    return cursor.fetchone()


def get_user_active_auction_count(user_id):
    init_auction_house()
    cursor.execute("""
    SELECT COUNT(*) AS cnt
    FROM auction_lots
    WHERE seller_user_id=? AND status=?
    """, (
        user_id,
        AUCTION_STATUS_ACTIVE,
    ))
    row = cursor.fetchone()
    try:
        return int(row["cnt"] or 0)
    except Exception:
        return int(row[0] or 0) if row else 0


def can_user_create_auction_lot(user_id):
    active_count = get_user_active_auction_count(user_id)

    if active_count >= AUCTION_MAX_ACTIVE_LOTS_PER_USER:
        return {
            "success": False,
            "message": f"❌ Досягнуто ліміт активних лотів: {AUCTION_MAX_ACTIVE_LOTS_PER_USER}.",
            "active_count": active_count,
        }

    return {
        "success": True,
        "active_count": active_count,
        "limit": AUCTION_MAX_ACTIVE_LOTS_PER_USER,
    }


def get_auction_lots(
    status=AUCTION_STATUS_ACTIVE,
    category=None,
    search_text=None,
    limit=10,
    offset=0,
    sort="new",
):
    init_auction_house()

    try:
        limit = int(limit)
    except Exception:
        limit = 10
    try:
        offset = int(offset)
    except Exception:
        offset = 0

    limit = max(1, min(50, limit))
    offset = max(0, offset)

    where = ["status=?"]
    params = [status]

    if category:
        where.append("category=?")
        params.append(normalize_auction_category(category))

    if search_text:
        where.append("item_name_norm LIKE ?")
        params.append(f"%{str(search_text).strip().lower()}%")

    order_by = "created_at DESC"
    if sort == "old":
        order_by = "created_at ASC"
    elif sort == "price_asc":
        order_by = "CAST(price AS REAL) ASC, created_at DESC"
    elif sort == "price_desc":
        order_by = "CAST(price AS REAL) DESC, created_at DESC"
    elif sort == "rarity":
        order_by = "rarity DESC, created_at DESC"

    sql = f"""
    SELECT *
    FROM auction_lots
    WHERE {' AND '.join(where)}
    ORDER BY {order_by}
    LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    cursor.execute(sql, tuple(params))
    return cursor.fetchall()


# ==============================
# WRITE HELPERS
# ==============================

def create_auction_lot_record(
    seller_user_id,
    item_type,
    item_snapshot,
    item_name,
    category,
    price,
    quantity=1,
    item_source="",
    item_ref_id=None,
    rarity="",
    level=0,
    enhancement_level=0,
    durability_current=None,
    durability_max=None,
):
    """
    Creates only the auction lot record.

    IMPORTANT:
    This helper does not remove or lock the item from inventory yet.
    Item movement/locking will be implemented in later patches.
    """

    init_auction_house()

    can_create = can_user_create_auction_lot(seller_user_id)
    if not can_create.get("success"):
        return can_create

    price_result = validate_auction_price(price)
    if not price_result.get("success"):
        return price_result

    category = normalize_auction_category(category)

    try:
        quantity = int(quantity or 1)
    except Exception:
        quantity = 1

    if quantity <= 0:
        return {
            "success": False,
            "message": "❌ Кількість має бути більшою за 0.",
        }

    item_name = str(item_name or "").strip()
    if not item_name:
        return {
            "success": False,
            "message": "❌ Назва предмета не може бути порожньою.",
        }

    now = now_iso()
    expires_at = iso_after_days(AUCTION_ACTIVE_DAYS)

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
        seller_user_id,
        str(item_type or ""),
        str(item_source or ""),
        item_ref_id,
        safe_json_dumps(item_snapshot or {}),
        item_name,
        item_name.lower(),
        category,
        str(rarity or ""),
        int(level or 0),
        int(enhancement_level or 0),
        durability_current,
        durability_max,
        quantity,
        price_result["price"],
        AUCTION_STATUS_ACTIVE,
        now,
        expires_at,
        now,
    ))

    lot_id = cursor.lastrowid
    conn.commit()

    add_auction_history(
        lot_id=lot_id,
        event_type=AUCTION_HISTORY_LISTED,
        actor_user_id=seller_user_id,
        seller_user_id=seller_user_id,
        item_name=item_name,
        category=category,
        quantity=quantity,
        price=price_result["price"],
        status_before=None,
        status_after=AUCTION_STATUS_ACTIVE,
        details={"item_type": item_type, "item_source": item_source, "item_ref_id": item_ref_id},
    )

    return {
        "success": True,
        "lot_id": lot_id,
        "message": "✅ Лот створено.",
    }


def mark_auction_lot_status(lot_id, status_after, actor_user_id=None, event_type=None, details=None):
    init_auction_house()

    lot = get_auction_lot_by_id(lot_id)
    if not lot:
        return {
            "success": False,
            "message": "❌ Лот не знайдено.",
        }

    status_before = lot["status"]
    now = now_iso()

    delete_after = lot["delete_after"]
    claimed_at = lot["claimed_at"]

    if status_after in [AUCTION_STATUS_EXPIRED_UNCLAIMED, AUCTION_STATUS_SOLD_UNCLAIMED]:
        delete_after = iso_after_days(AUCTION_CLAIM_DAYS)

    if status_after in [AUCTION_STATUS_EXPIRED_CLAIMED, AUCTION_STATUS_SOLD_CLAIMED]:
        claimed_at = now

    cursor.execute("""
    UPDATE auction_lots
    SET status=?,
        claimed_at=?,
        delete_after=?,
        updated_at=?
    WHERE id=?
    """, (
        status_after,
        claimed_at,
        delete_after,
        now,
        lot_id,
    ))
    conn.commit()

    add_auction_history(
        lot_id=lot_id,
        event_type=event_type or status_after,
        actor_user_id=actor_user_id,
        seller_user_id=lot["seller_user_id"],
        buyer_user_id=lot["buyer_user_id"],
        item_name=lot["item_name"],
        category=lot["category"],
        quantity=lot["quantity"],
        price=lot["price"],
        status_before=status_before,
        status_after=status_after,
        details=details or {},
    )

    return {
        "success": True,
        "message": "✅ Статус лота оновлено.",
    }


def update_expired_auction_lots():
    """
    Expiration cleanup:
    - ACTIVE after 7 days -> EXPIRED_UNCLAIMED
    - EXPIRED_UNCLAIMED after 30 days -> DELETED
    - SOLD_UNCLAIMED after 30 days -> DELETED

    No automatic item/gold return is performed here.
    """

    init_auction_house()
    now = now_iso()

    expired_count = 0
    deleted_count = 0

    cursor.execute("""
    SELECT *
    FROM auction_lots
    WHERE status=? AND expires_at<=?
    """, (
        AUCTION_STATUS_ACTIVE,
        now,
    ))
    active_rows = cursor.fetchall()

    for lot in active_rows:
        cursor.execute("""
        UPDATE auction_lots
        SET status=?,
            delete_after=?,
            updated_at=?
        WHERE id=? AND status=?
        """, (
            AUCTION_STATUS_EXPIRED_UNCLAIMED,
            iso_after_days(AUCTION_CLAIM_DAYS),
            now,
            lot["id"],
            AUCTION_STATUS_ACTIVE,
        ))

        if cursor.rowcount:
            expired_count += 1
            add_auction_history(
                lot_id=lot["id"],
                event_type=AUCTION_HISTORY_EXPIRED,
                seller_user_id=lot["seller_user_id"],
                buyer_user_id=lot["buyer_user_id"],
                item_name=lot["item_name"],
                category=lot["category"],
                quantity=lot["quantity"],
                price=lot["price"],
                status_before=AUCTION_STATUS_ACTIVE,
                status_after=AUCTION_STATUS_EXPIRED_UNCLAIMED,
            )

    cursor.execute("""
    SELECT *
    FROM auction_lots
    WHERE status IN (?, ?) AND delete_after IS NOT NULL AND delete_after<=?
    """, (
        AUCTION_STATUS_EXPIRED_UNCLAIMED,
        AUCTION_STATUS_SOLD_UNCLAIMED,
        now,
    ))
    delete_rows = cursor.fetchall()

    for lot in delete_rows:
        before = lot["status"]
        cursor.execute("""
        UPDATE auction_lots
        SET status=?, updated_at=?
        WHERE id=? AND status=?
        """, (
            AUCTION_STATUS_DELETED,
            now,
            lot["id"],
            before,
        ))

        if cursor.rowcount:
            deleted_count += 1
            add_auction_history(
                lot_id=lot["id"],
                event_type=AUCTION_HISTORY_DELETED,
                seller_user_id=lot["seller_user_id"],
                buyer_user_id=lot["buyer_user_id"],
                item_name=lot["item_name"],
                category=lot["category"],
                quantity=lot["quantity"],
                price=lot["price"],
                status_before=before,
                status_after=AUCTION_STATUS_DELETED,
            )

    conn.commit()

    return {
        "success": True,
        "expired": expired_count,
        "deleted": deleted_count,
    }


def get_auction_house_stats():
    init_auction_house()

    result = {}
    statuses = [
        AUCTION_STATUS_ACTIVE,
        AUCTION_STATUS_SOLD_UNCLAIMED,
        AUCTION_STATUS_SOLD_CLAIMED,
        AUCTION_STATUS_EXPIRED_UNCLAIMED,
        AUCTION_STATUS_EXPIRED_CLAIMED,
        AUCTION_STATUS_DELETED,
    ]

    for status in statuses:
        cursor.execute("SELECT COUNT(*) AS cnt FROM auction_lots WHERE status=?", (status,))
        row = cursor.fetchone()
        try:
            result[status] = int(row["cnt"] or 0)
        except Exception:
            result[status] = int(row[0] or 0) if row else 0

    return result


# Ensure tables exist when module is imported.
try:
    init_auction_house()
except Exception as _auction_init_error:
    print(f"⚠️ Auction house init failed: {_auction_init_error}")
'''

DB_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE DB WRAPPERS V1
# ==============================

# 8.0.1 wrappers. Heavy auction logic lives in systems/auction_house_system.py
# to avoid overloading db.py.


def init_auction_house():
    from systems.auction_house_system import init_auction_house as _init_auction_house
    return _init_auction_house()


def validate_auction_price(value):
    from systems.auction_house_system import validate_auction_price as _validate_auction_price
    return _validate_auction_price(value)


def decimal_to_price_text(value):
    from systems.auction_house_system import decimal_to_price_text as _decimal_to_price_text
    return _decimal_to_price_text(value)


def auction_price_to_decimal(value):
    from systems.auction_house_system import auction_price_to_decimal as _auction_price_to_decimal
    return _auction_price_to_decimal(value)


def normalize_auction_category(category):
    from systems.auction_house_system import normalize_auction_category as _normalize_auction_category
    return _normalize_auction_category(category)


def add_auction_history(**kwargs):
    from systems.auction_house_system import add_auction_history as _add_auction_history
    return _add_auction_history(**kwargs)


def get_auction_lot_by_id(lot_id):
    from systems.auction_house_system import get_auction_lot_by_id as _get_auction_lot_by_id
    return _get_auction_lot_by_id(lot_id)


def get_user_active_auction_count(user_id):
    from systems.auction_house_system import get_user_active_auction_count as _get_user_active_auction_count
    return _get_user_active_auction_count(user_id)


def can_user_create_auction_lot(user_id):
    from systems.auction_house_system import can_user_create_auction_lot as _can_user_create_auction_lot
    return _can_user_create_auction_lot(user_id)


def get_auction_lots(status="ACTIVE", category=None, search_text=None, limit=10, offset=0, sort="new"):
    from systems.auction_house_system import get_auction_lots as _get_auction_lots
    return _get_auction_lots(status=status, category=category, search_text=search_text, limit=limit, offset=offset, sort=sort)


def create_auction_lot_record(**kwargs):
    from systems.auction_house_system import create_auction_lot_record as _create_auction_lot_record
    return _create_auction_lot_record(**kwargs)


def mark_auction_lot_status(lot_id, status_after, actor_user_id=None, event_type=None, details=None):
    from systems.auction_house_system import mark_auction_lot_status as _mark_auction_lot_status
    return _mark_auction_lot_status(lot_id, status_after, actor_user_id=actor_user_id, event_type=event_type, details=details)


def update_expired_auction_lots():
    from systems.auction_house_system import update_expired_auction_lots as _update_expired_auction_lots
    return _update_expired_auction_lots()


def get_auction_house_stats():
    from systems.auction_house_system import get_auction_house_stats as _get_auction_house_stats
    return _get_auction_house_stats()
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def write_system_file(root):
    target = root / SYSTEM_PATH
    target.parent.mkdir(exist_ok=True)
    original = target.read_text(encoding="utf-8") if target.exists() else None
    backup = make_backup(root, target) if target.exists() else None
    target.write_text(SYSTEM_CODE.strip() + "\n", encoding="utf-8")
    return target, backup, original, True


def patch_db_wrappers(root):
    target = root / "db.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py")

    original = target.read_text(encoding="utf-8")

    if DB_MARKER in original:
        return target, None, original, False

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + DB_APPEND + "\n", encoding="utf-8")
    return target, backup, original, True


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        for patch_func in [write_system_file, patch_db_wrappers]:
            file_path, backup, original, changed = patch_func(root)
            if changed:
                changed_files.append(file_path)
                originals.append((file_path, original))
            if backup:
                backups.append(backup)

        unique_files = []
        for file_path in changed_files:
            if file_path not in unique_files:
                unique_files.append(file_path)

        for file_path in unique_files:
            py_compile.compile(str(file_path), doraise=True)

        sys.path.insert(0, str(root))
        from db import init_auction_house, get_auction_house_stats
        init_auction_house()
        stats = get_auction_house_stats()

    except Exception as error:
        for file_path, original in originals:
            try:
                if original is None:
                    file_path.unlink(missing_ok=True)
                else:
                    file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass
        raise SystemExit(
            "❌ Помилка під час patch_8_0_1_auction_core_db.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.1 Auction Core DB застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nСтворено ядро Торгового Дому:")
    print("- systems/auction_house_system.py")
    print("- auction_lots")
    print("- auction_history")
    print("- Decimal price validation")
    print("- active lot limit = 20")
    print("- active lot duration = 7 days")
    print("- unclaimed item/gold retention = 30 days")
    print("- expiration cleanup helper")
    print("- db.py містить тільки тонкі wrappers")

    print("\nCurrent auction stats:")
    for key, value in stats.items():
        print(f"- {key}: {value}")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("python -m py_compile .\\db.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
