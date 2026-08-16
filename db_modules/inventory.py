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

def add_item(user_id, item_id, quantity=1, durability=100):
    """
    Додає предмет в інвентар.
    Підтримує стакування.
    """
    capacity = get_bag_capacity(user_id)
    used_slots = get_inventory_used_slots(user_id)
    
    if used_slots >= capacity:
        return {
            "success": False,
            "message": "🎒 Сумка переповнена!"
        }
    
    # Get item info
    item = get_item(item_id)
    
    if not item:
        return {
            "success": False,
            "message": "❌ Предмет не знайдено."
        }
    
    max_stack = item[6] if len(item) > 6 else 1  # max_stack field
    
    try:
        max_stack = int(max_stack or 1)
    except Exception:
        max_stack = 1
    
    # If stackable, try to add to existing stack
    if max_stack > 1:
        cursor.execute("""
        SELECT id, quantity
        FROM inventory
        WHERE user_id=? AND item_id=? AND quantity < ?
        ORDER BY quantity DESC
        LIMIT 1
        """, (user_id, item_id, max_stack))
        
        existing = cursor.fetchone()
        
        if existing:
            inventory_id, current_quantity = existing
            
            try:
                current_quantity = int(current_quantity or 0)
            except Exception:
                current_quantity = 0
            
            space_in_stack = max_stack - current_quantity
            
            if space_in_stack > 0:
                add_to_stack = min(quantity, space_in_stack)
                new_quantity = current_quantity + add_to_stack
                
                cursor.execute("""
                UPDATE inventory
                SET quantity=?
                WHERE id=?
                """, (new_quantity, inventory_id))
                
                conn.commit()
                
                quantity -= add_to_stack
                
                if quantity <= 0:
                    return {
                        "success": True,
                        "message": f"✅ Додано {item[1]} x{add_to_stack}"
                    }
    
    # Create new stack
    if quantity > 0:
        cursor.execute("""
        INSERT INTO inventory (user_id, item_id, quantity, durability)
        VALUES (?, ?, ?, ?)
        """, (user_id, item_id, quantity, durability))
        
        conn.commit()
        
        return {
            "success": True,
            "message": f"✅ Додано {item[1]} x{quantity}"
        }
    
    return {
        "success": True,
        "message": "✅ Предмет додано"
    }


# ==============================
# CONSUME ITEMS
# ==============================

def consume_inventory_item(inventory_id, amount=1):
    """
    Використовує предмет з інвентаря.
    Зменшує кількість або видаляє стак.
    """
    cursor.execute("""
    SELECT quantity
    FROM inventory
    WHERE id=?
    """, (inventory_id,))
    
    row = cursor.fetchone()
    
    if not row:
        return False
    
    try:
        quantity = int(row[0] or 0)
    except Exception:
        quantity = 0
    
    if quantity <= amount:
        # Delete stack
        cursor.execute("""
        DELETE FROM inventory
        WHERE id=?
        """, (inventory_id,))
    else:
        # Decrease quantity
        new_quantity = quantity - amount
        
        cursor.execute("""
        UPDATE inventory
        SET quantity=?
        WHERE id=?
        """, (new_quantity, inventory_id))
    
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
