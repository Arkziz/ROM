"""
Inventory management module
"""

from .connection import conn, cursor


# ==============================
# INVENTORY CAPACITY
# ==============================

def get_bag_capacity(user_id):
    """Повертає максимальну ємність сумки."""
    cursor.execute("""
    SELECT bag_slots
    FROM users
    WHERE user_id=?
    """, (user_id,))
    
    row = cursor.fetchone()
    
    if not row:
        return 40  # DEFAULT_BAG_SLOTS
    
    try:
        capacity = int(row[0] or 40)
    except Exception:
        capacity = 40
    
    return max(40, capacity)


def get_inventory_used_slots(user_id):
    """Рахує зайняті слоти в інвентарі."""
    cursor.execute("""
    SELECT COUNT(*)
    FROM inventory
    WHERE user_id=?
    """, (user_id,))
    
    row = cursor.fetchone()
    
    if not row:
        return 0
    
    try:
        return int(row[0] or 0)
    except Exception:
        return 0


# ==============================
# INVENTORY QUERIES
# ==============================

def get_inventory(user_id):
    """Отримує інвентар гравця."""
    cursor.execute("""
    SELECT
        inventory.id,
        inventory.item_id,
        inventory.quantity,
        inventory.durability,
        items.name,
        items.type,
        items.rarity,
        items.category
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.user_id=?
    ORDER BY inventory.id ASC
    """, (user_id,))
    
    return cursor.fetchall()


def get_item(item_id):
    """Отримує інформацію про предмет."""
    cursor.execute("""
    SELECT *
    FROM items
    WHERE id=?
    """, (item_id,))
    
    return cursor.fetchone()


# ==============================
# ADD ITEMS
# ==============================


# ROM 17.2.0 CANONICAL STACK NORMALIZATION

def _inventory_table_exists(table_name):
    row = cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (str(table_name),),
    ).fetchone()
    return bool(row)


def _inventory_reserved_ids_for_item(user_id, item_id):
    """Return reserved row IDs; a reservation protects the whole user/item group."""
    if not _inventory_table_exists("inventory_reservations"):
        return set()
    try:
        rows = cursor.execute(
            """
            SELECT DISTINCT r.inventory_id
            FROM inventory_reservations AS r
            JOIN inventory AS inv ON inv.id=r.inventory_id
            WHERE inv.user_id=? AND inv.item_id=? AND COALESCE(r.quantity, 0)>0
            """,
            (int(user_id), int(item_id)),
        ).fetchall()
        return {int(row[0]) for row in rows}
    except Exception:
        return set()


def _inventory_required_new_stacks(quantity, free_space, max_stack):
    remaining = max(0, int(quantity) - max(0, int(free_space)))
    if remaining <= 0:
        return 0
    return (remaining + int(max_stack) - 1) // int(max_stack)

def add_item(user_id, item_id, quantity=1, durability=100):
    """Atomically add items, respecting max_stack and the canonical award result contract."""
    # ROM 17.2.0.3 CENTRAL DROP STACK AWARD CONTRACT RECOVERY
    try:
        user_id = int(user_id)
        item_id = int(item_id)
        quantity = int(quantity)
    except Exception:
        return {"success": False, "name": "Предмет", "added": 0, "lost": 0,
                "message": "❌ Некоректні дані предмета."}
    if quantity <= 0:
        return {"success": False, "name": "Предмет", "added": 0, "lost": 0,
                "message": "❌ Кількість має бути більшою за нуль."}

    # Never use positional SELECT * indexes for max_stack. The items schema puts
    # weapon_hands before max_stack, which previously made every rune/potion act
    # as max_stack=1 during runtime awards.
    item = cursor.execute(
        "SELECT name, COALESCE(max_stack, 1) FROM items WHERE id=?",
        (item_id,),
    ).fetchone()
    if not item:
        return {"success": False, "name": "Предмет", "added": 0, "lost": quantity,
                "message": "❌ Предмет не знайдено."}
    name = str(item[0] or "Предмет")
    max_stack = max(1, int(item[1] or 1))
    requested = quantity
    savepoint = "rom_add_item_17_2_0_3"

    try:
        cursor.execute(f"SAVEPOINT {savepoint}")
        capacity = get_bag_capacity(user_id)
        used_slots = get_inventory_used_slots(user_id)
        partial = []
        free_space = 0

        if max_stack > 1 and not _inventory_reserved_ids_for_item(user_id, item_id):
            partial = cursor.execute(
                """SELECT id, quantity FROM inventory
                   WHERE user_id=? AND item_id=? AND quantity>0 AND quantity<?
                   ORDER BY id ASC""",
                (user_id, item_id, max_stack),
            ).fetchall()
            free_space = sum(max(0, max_stack-int(row[1] or 0)) for row in partial)

        new_stacks = _inventory_required_new_stacks(quantity, free_space, max_stack)
        if used_slots + new_stacks > capacity:
            cursor.execute(f"ROLLBACK TO {savepoint}")
            cursor.execute(f"RELEASE {savepoint}")
            return {"success": False, "name": name, "added": 0, "lost": requested,
                    "used_slots": used_slots, "capacity": capacity,
                    "message": "🎒 Сумка переповнена!"}

        first_inventory_id = None
        for inventory_id, current in partial:
            if quantity <= 0:
                break
            current = max(0, int(current or 0))
            moved = min(quantity, max_stack-current)
            if moved:
                cursor.execute(
                    "UPDATE inventory SET quantity=? WHERE id=? AND user_id=? AND item_id=?",
                    (current+moved, int(inventory_id), user_id, item_id),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("Не вдалося оновити існуючий стак.")
                first_inventory_id = first_inventory_id or int(inventory_id)
                quantity -= moved

        while quantity > 0:
            stack_quantity = min(quantity, max_stack)
            cursor.execute(
                "INSERT INTO inventory (user_id,item_id,quantity,durability) VALUES (?,?,?,?)",
                (user_id,item_id,stack_quantity,durability),
            )
            first_inventory_id = first_inventory_id or int(cursor.lastrowid)
            quantity -= stack_quantity

        cursor.execute(f"RELEASE {savepoint}")
        conn.commit()
        return {"success": True, "name": name, "added": requested, "lost": 0,
                "inventory_id": first_inventory_id,
                "used_slots": get_inventory_used_slots(user_id), "capacity": capacity,
                "message": f"✅ Додано {name} x{requested}"}
    except Exception as error:
        try:
            cursor.execute(f"ROLLBACK TO {savepoint}")
            cursor.execute(f"RELEASE {savepoint}")
        except Exception:
            conn.rollback()
        return {"success": False, "name": name, "added": 0, "lost": requested,
                "message": f"❌ Не вдалося додати предмет: {error}"}





# ==============================
# CONSUME ITEMS
# ==============================

def consume_inventory_item(user_id_or_inventory_id, inventory_id_or_amount=1, amount=None):
    """Consume an inventory stack with both historical signatures.

    Supported:
    - consume_inventory_item(inventory_id, amount=1)
    - consume_inventory_item(user_id, inventory_id, amount=1)
    """
    if amount is None:
        user_id = None
        inventory_id = int(user_id_or_inventory_id)
        amount = int(inventory_id_or_amount)
    else:
        user_id = int(user_id_or_inventory_id)
        inventory_id = int(inventory_id_or_amount)
        amount = int(amount)

    if amount <= 0:
        return False

    if user_id is None:
        cursor.execute("SELECT quantity FROM inventory WHERE id=?", (inventory_id,))
    else:
        cursor.execute(
            "SELECT quantity FROM inventory WHERE id=? AND user_id=?",
            (inventory_id, user_id),
        )
    row = cursor.fetchone()
    if not row:
        return False

    try:
        quantity = int(row[0] or 0)
    except Exception:
        quantity = 0
    if quantity < amount:
        return False

    if quantity == amount:
        if user_id is None:
            cursor.execute("DELETE FROM inventory WHERE id=?", (inventory_id,))
        else:
            cursor.execute(
                "DELETE FROM inventory WHERE id=? AND user_id=?",
                (inventory_id, user_id),
            )
    else:
        new_quantity = quantity - amount
        if user_id is None:
            cursor.execute(
                "UPDATE inventory SET quantity=? WHERE id=?",
                (new_quantity, inventory_id),
            )
        else:
            cursor.execute(
                "UPDATE inventory SET quantity=? WHERE id=? AND user_id=?",
                (new_quantity, inventory_id, user_id),
            )
    conn.commit()
    return True


def count_user_item(user_id, item_id):
    """Рахує кількість предмета у користувача."""
    cursor.execute("""
    SELECT COALESCE(SUM(quantity), 0)
    FROM inventory
    WHERE user_id=? AND item_id=?
    """, (user_id, item_id))
    
    row = cursor.fetchone()
    
    try:
        return int((row[0] if row else 0) or 0)
    except Exception:
        return 0


def consume_user_item_by_item_id(user_id, item_id, quantity=1):
    """
    Споживає предмет за item_id (може бути в різних стаках).
    """
    try:
        quantity = int(quantity)
    except Exception:
        quantity = 1
    
    if quantity <= 0:
        return True
    
    if count_user_item(user_id, item_id) < quantity:
        return False
    
    remaining = quantity
    
    cursor.execute("""
    SELECT id, quantity
    FROM inventory
    WHERE user_id=? AND item_id=?
    ORDER BY id ASC
    """, (user_id, item_id))
    
    rows = cursor.fetchall()
    
    for inventory_id, stack_quantity in rows:
        if remaining <= 0:
            break
        
        stack_quantity = int(stack_quantity or 0)
        take = min(stack_quantity, remaining)
        new_quantity = stack_quantity - take
        
        if new_quantity <= 0:
            cursor.execute("""
            DELETE FROM inventory
            WHERE id=?
            """, (inventory_id,))
        else:
            cursor.execute("""
            UPDATE inventory
            SET quantity=?
            WHERE id=?
            """, (new_quantity, inventory_id))
        
        remaining -= take
    
    conn.commit()
    
    return remaining <= 0


# ==============================
# FIND ITEMS
# ==============================

def find_first_item_stack_by_type(user_id, item_type):
    """
    Знаходить перший стак предмета за типом.
    """
    cursor.execute("""
    SELECT inventory.id, items.id, items.name
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.user_id=? AND items.type=?
    ORDER BY inventory.id ASC
    LIMIT 1
    """, (user_id, item_type))
    
    return cursor.fetchone()


# ==============================
# SELL ITEMS
# ==============================

def sell_all_trash(user_id):
    """
    Продає всі trash предмети з інвентаря користувача.
    Повертає інформацію про продані предмети та отримане золото.
    """
    cursor.execute("""
    SELECT
        inventory.id,
        items.name,
        inventory.quantity,
        items.sell_price
    FROM inventory
    JOIN items ON inventory.item_id = items.id
    WHERE inventory.user_id=?
      AND items.category='trash'
    """, (user_id,))

    rows = cursor.fetchall()

    if not rows:
        return {
            "sold_items_count": 0,
            "gold_earned": 0.0,
            "freed_slots": 0,
            "details": []
        }

    total_gold = 0.0
    freed_slots = 0
    details = []

    for inv_id, name, quantity, sell_price in rows:
        quantity = quantity or 1
        sell_price = sell_price or 0

        earned = quantity * sell_price
        total_gold += earned
        freed_slots += 1

        details.append(f"{name} x{quantity} = {earned:.2f} золота")

        cursor.execute("""
        DELETE FROM inventory
        WHERE id=?
        """, (inv_id,))

    cursor.execute("""
    UPDATE users
    SET gold = gold + ?
    WHERE user_id=?
    """, (total_gold, user_id))

    conn.commit()

    return {
        "sold_items_count": len(rows),
        "gold_earned": total_gold,
        "freed_slots": freed_slots,
        "details": details
    }
