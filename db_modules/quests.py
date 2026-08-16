"""
Daily quests and contracts system
"""

from .connection import conn, cursor
from .utils import get_daily_today_str


# ==============================
# DAILY QUEST SYSTEM
# ==============================

def init_daily_quest_system():
    """Ініціалізує таблиці та колонки для щоденних квестів."""
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_daily_quests (
            user_id INTEGER PRIMARY KEY,
            daily_key TEXT NOT NULL,
            total_kills INTEGER DEFAULT 0,
            elite_kills INTEGER DEFAULT 0,
            pvp_kills INTEGER DEFAULT 0,
            trades_completed INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            claimed_at TEXT DEFAULT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_udq_user_daily
        ON user_daily_quests(user_id, daily_key)
        """)
        
        conn.commit()
    except Exception:
        pass


def get_user_daily_quest(user_id):
    """Отримує поточний щоденний квест гравця."""
    init_daily_quest_system()
    
    today = get_daily_today_str()
    
    cursor.execute("""
    SELECT user_id, daily_key, total_kills, elite_kills, pvp_kills, 
           trades_completed, status, claimed_at
    FROM user_daily_quests
    WHERE user_id=? AND daily_key=?
    """, (user_id, today))
    
    row = cursor.fetchone()
    if not row:
        # Create new quest for today
        cursor.execute("""
        INSERT INTO user_daily_quests 
        (user_id, daily_key, total_kills, elite_kills, pvp_kills, trades_completed, status)
        VALUES (?, ?, 0, 0, 0, 0, 'active')
        """, (user_id, today))
        conn.commit()
        
        return {
            "user_id": user_id,
            "daily_key": today,
            "total_kills": 0,
            "elite_kills": 0,
            "pvp_kills": 0,
            "trades_completed": 0,
            "status": "active",
            "claimed_at": None
        }
    
    return {
        "user_id": row[0],
        "daily_key": row[1],
        "total_kills": row[2],
        "elite_kills": row[3],
        "pvp_kills": row[4],
        "trades_completed": row[5],
        "status": row[6],
        "claimed_at": row[7]
    }


def add_daily_quest_progress(user_id, total_kills=0, elite_kills=0, pvp_kills=0, trades=0):
    """Додає прогрес до щоденного квесту."""
    init_daily_quest_system()
    
    today = get_daily_today_str()
    quest = get_user_daily_quest(user_id)
    
    cursor.execute("""
    UPDATE user_daily_quests
    SET total_kills = total_kills + ?,
        elite_kills = elite_kills + ?,
        pvp_kills = pvp_kills + ?,
        trades_completed = trades_completed + ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id=? AND daily_key=?
    """, (total_kills, elite_kills, pvp_kills, trades, user_id, today))
    
    conn.commit()


def is_daily_quest_complete(user_id):
    """Перевіряє чи виконано щоденний квест."""
    from data.balance import DAILY_QUEST_REQUIREMENTS
    
    quest = get_user_daily_quest(user_id)
    
    if quest["status"] != "active":
        return False
    
    return (
        quest["total_kills"] >= DAILY_QUEST_REQUIREMENTS["total_kills"] and
        quest["elite_kills"] >= DAILY_QUEST_REQUIREMENTS["elite_kills"]
    )


def claim_daily_quest_reward(user_id):
    """Отримує винагороду за щоденний квест. Returns (success, message, rewards)"""
    from data.balance import DAILY_QUEST_REWARDS
    from .inventory import add_item
    from .player import add_gold
    
    quest = get_user_daily_quest(user_id)
    
    if quest["status"] == "claimed":
        return (False, "⚠️ Ви вже отримали винагороду за сьогодні!", None)
    
    if not is_daily_quest_complete(user_id):
        return (False, "⚠️ Квест ще не виконано!", None)
    
    # Award rewards
    rewards = {}
    
    # Gold
    if "gold" in DAILY_QUEST_REWARDS:
        gold_amount = DAILY_QUEST_REWARDS["gold"]
        add_gold(user_id, gold_amount)
        rewards["gold"] = gold_amount
    
    # Items
    if "items" in DAILY_QUEST_REWARDS:
        rewards["items"] = []
        for item_id, quantity in DAILY_QUEST_REWARDS["items"]:
            add_item(user_id, item_id, quantity)
            rewards["items"].append((item_id, quantity))
    
    # Mark as claimed
    today = get_daily_today_str()
    cursor.execute("""
    UPDATE user_daily_quests
    SET status = 'claimed',
        claimed_at = CURRENT_TIMESTAMP
    WHERE user_id=? AND daily_key=?
    """, (user_id, today))
    conn.commit()
    
    return (True, "✅ Винагорода отримана!", rewards)


def get_daily_quest_progress_text(user_id):
    """Форматує текстовий опис прогресу квесту."""
    from data.balance import DAILY_QUEST_REQUIREMENTS
    
    quest = get_user_daily_quest(user_id)
    
    progress_lines = []
    progress_lines.append("📋 **Щоденний Квест**\n")
    
    if quest["status"] == "claimed":
        progress_lines.append("✅ Квест виконано та винагороду отримано!")
        return "\n".join(progress_lines)
    
    # Total kills
    total_req = DAILY_QUEST_REQUIREMENTS["total_kills"]
    total_current = min(quest["total_kills"], total_req)
    total_icon = "✅" if total_current >= total_req else "⏳"
    progress_lines.append(f"{total_icon} Загальні вбивства: {total_current}/{total_req}")
    
    # Elite kills
    elite_req = DAILY_QUEST_REQUIREMENTS["elite_kills"]
    elite_current = min(quest["elite_kills"], elite_req)
    elite_icon = "✅" if elite_current >= elite_req else "⏳"
    progress_lines.append(f"{elite_icon} Еліта: {elite_current}/{elite_req}")
    
    if is_daily_quest_complete(user_id):
        progress_lines.append("\n🎁 **Квест виконано! Отримайте винагороду!**")
    
    return "\n".join(progress_lines)


def cleanup_old_daily_quests(days_to_keep=7):
    """Видаляє старі квести (cleanup функція)."""
    init_daily_quest_system()
    
    cursor.execute("""
    DELETE FROM user_daily_quests
    WHERE created_at < date('now', '-' || ? || ' days')
    """, (days_to_keep,))
    
    deleted = cursor.rowcount
    conn.commit()
    
    return deleted


def process_daily_quest_progress_on_kill(user_id, mob=None):
    """
    Викликається після перемоги над будь-яким монстром.

    Враховуються:
    - звичайні монстри
    - елітні монстри
    - боси, коли вони будуть реалізовані
    """
    reset_daily_quest_if_needed(user_id)

    status = get_daily_quest_status(user_id)

    if not status["exists"]:
        return {
            "updated": False,
            "completed": False,
            "message": None
        }

    if status["reward_claimed"]:
        return {
            "updated": False,
            "completed": False,
            "message": None
        }

    if status["completed"]:
        return {
            "updated": False,
            "completed": True,
            "message": None
        }

    progress = status["progress"]
    target_count = status["target_count"]

    new_progress = min(target_count, progress + 1)
    completed = 1 if new_progress >= target_count else 0

    cursor.execute("""
    UPDATE user_daily_quests
    SET progress=?,
        completed=?
    WHERE user_id=?
    """, (
        new_progress,
        completed,
        user_id
    ))

    conn.commit()

    if completed:
        return {
            "updated": True,
            "completed": True,
            "message": (
                "📆 Щоденне завдання виконано!\n"
                "✅ Прогрес: 25/25\n"
                "🏛️ Поверніться до Ратуші за нагородою."
            )
        }

    return {
        "updated": True,
        "completed": False,
        "message": f"📆 Щоденне завдання: {new_progress}/{target_count}"
    }

