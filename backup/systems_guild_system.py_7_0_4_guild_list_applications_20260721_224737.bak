from datetime import datetime

from db import conn, cursor


# ==============================
# ✅ GUILD SQLITE ROW FACTORY FIX V1
# ==============================

# 7.0.3a
# У проєкті sqlite cursor може повертати tuple, а guild_system працює з row["field"].
# sqlite3.Row підтримує обидва формати доступу:
# - row["guild_id"]
# - row[0]
# Тому це безпечний fix для гільдійних таблиць і сумісний зі старим кодом.

import sqlite3 as _guild_sqlite3

try:
    conn.row_factory = _guild_sqlite3.Row
except Exception:
    pass

try:
    cursor.row_factory = _guild_sqlite3.Row
except Exception:
    pass



GUILD_CREATE_COST_GOLD = 0
DEFAULT_GUILD_MEMBER_LIMIT = 30
GUILD_ROLE_LEADER = "leader"
GUILD_ROLE_OFFICER = "officer"
GUILD_ROLE_MEMBER = "member"

GUILD_APPLICATION_PENDING = "pending"
GUILD_APPLICATION_ACCEPTED = "accepted"
GUILD_APPLICATION_REJECTED = "rejected"
GUILD_APPLICATION_CANCELLED = "cancelled"


# ==============================
# ✅ TIME / NORMALIZATION
# ==============================

def now_iso():
    return datetime.now().isoformat()


def get_current_guild_season_key():
    """
    Поточний місячний сезон рейтингу гільдій.
    Формат: YYYY-MM
    """

    return datetime.now().strftime("%Y-%m")


def normalize_guild_name(value):
    return (value or "").strip().casefold()


def normalize_guild_tag(value):
    return (value or "").strip().upper()


def calculate_guild_score(exp=0, resource=0, kills=0, contracts=0):
    """
    Єдина формула score для рейтингу.

    Стартова проста формула:
    score = exp + resource + kills + contracts * 25

    Її можна буде змінити пізніше без перебудови таблиць.
    """

    exp = int(exp or 0)
    resource = int(resource or 0)
    kills = int(kills or 0)
    contracts = int(contracts or 0)

    return exp + resource + kills + contracts * 25


# ==============================
# ✅ INIT
# ==============================

def init_guild_system():
    """
    Ініціалізує таблиці гільдій.

    Безпечна для багаторазового виклику.
    """

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guilds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_norm TEXT NOT NULL UNIQUE,
        tag TEXT NOT NULL,
        tag_norm TEXT NOT NULL UNIQUE,
        icon TEXT DEFAULT '🏰',
        leader_user_id INTEGER NOT NULL,
        level INTEGER DEFAULT 1,
        exp INTEGER DEFAULT 0,
        resource INTEGER DEFAULT 0,
        member_limit INTEGER DEFAULT 30,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,

        monthly_exp INTEGER DEFAULT 0,
        monthly_resource INTEGER DEFAULT 0,
        monthly_kills INTEGER DEFAULT 0,
        monthly_contracts INTEGER DEFAULT 0,
        monthly_score INTEGER DEFAULT 0,

        total_exp INTEGER DEFAULT 0,
        total_resource INTEGER DEFAULT 0,
        total_kills INTEGER DEFAULT 0,
        total_contracts INTEGER DEFAULT 0,
        total_score INTEGER DEFAULT 0,

        season_key TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guild_members (
        guild_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL UNIQUE,
        role TEXT NOT NULL DEFAULT 'member',
        joined_at TEXT NOT NULL,

        contribution_exp INTEGER DEFAULT 0,
        contribution_resource INTEGER DEFAULT 0,
        contribution_kills INTEGER DEFAULT 0,
        contribution_contracts INTEGER DEFAULT 0,
        contribution_score INTEGER DEFAULT 0,

        monthly_contribution_exp INTEGER DEFAULT 0,
        monthly_contribution_resource INTEGER DEFAULT 0,
        monthly_contribution_kills INTEGER DEFAULT 0,
        monthly_contribution_contracts INTEGER DEFAULT 0,
        monthly_contribution_score INTEGER DEFAULT 0,

        PRIMARY KEY (guild_id, user_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guild_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL,
        processed_at TEXT,
        processed_by INTEGER,
        UNIQUE (guild_id, user_id, status)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guild_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guild_season_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        season_key TEXT NOT NULL,
        monthly_exp INTEGER DEFAULT 0,
        monthly_resource INTEGER DEFAULT 0,
        monthly_kills INTEGER DEFAULT 0,
        monthly_contracts INTEGER DEFAULT 0,
        monthly_score INTEGER DEFAULT 0,
        finished_at TEXT NOT NULL,
        UNIQUE (guild_id, season_key)
    )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_guilds_monthly_score ON guilds(monthly_score DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_guilds_total_score ON guilds(total_score DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_guild_members_user ON guild_members(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_guild_members_guild ON guild_members(guild_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_guild_applications_guild_status ON guild_applications(guild_id, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_guild_logs_guild_created ON guild_logs(guild_id, created_at DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_guild_season_history_season ON guild_season_history(season_key, monthly_score DESC)")

    conn.commit()

    ensure_all_guild_monthly_seasons()


# ==============================
# ✅ MONTHLY SEASON RESET
# ==============================

def archive_and_reset_guild_monthly_stats(guild_row, new_season_key=None):
    """
    Архівує минулий місяць у guild_season_history і обнуляє monthly counters.
    """

    if not guild_row:
        return False

    if new_season_key is None:
        new_season_key = get_current_guild_season_key()

    guild_id = guild_row["id"]
    old_season_key = guild_row["season_key"]

    if old_season_key == new_season_key:
        return False

    finished_at = now_iso()

    cursor.execute("""
    INSERT OR IGNORE INTO guild_season_history (
        guild_id,
        season_key,
        monthly_exp,
        monthly_resource,
        monthly_kills,
        monthly_contracts,
        monthly_score,
        finished_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        guild_id,
        old_season_key,
        int(guild_row["monthly_exp"] or 0),
        int(guild_row["monthly_resource"] or 0),
        int(guild_row["monthly_kills"] or 0),
        int(guild_row["monthly_contracts"] or 0),
        int(guild_row["monthly_score"] or 0),
        finished_at,
    ))

    cursor.execute("""
    UPDATE guilds
    SET monthly_exp=0,
        monthly_resource=0,
        monthly_kills=0,
        monthly_contracts=0,
        monthly_score=0,
        season_key=?,
        updated_at=?
    WHERE id=?
    """, (
        new_season_key,
        finished_at,
        guild_id,
    ))

    cursor.execute("""
    UPDATE guild_members
    SET monthly_contribution_exp=0,
        monthly_contribution_resource=0,
        monthly_contribution_kills=0,
        monthly_contribution_contracts=0,
        monthly_contribution_score=0
    WHERE guild_id=?
    """, (
        guild_id,
    ))

    conn.commit()

    add_guild_log(
        guild_id=guild_id,
        event_type="season_reset",
        text=f"Почався новий сезон рейтингу: {new_season_key}. Попередній сезон {old_season_key} збережено в історії."
    )

    return True


def ensure_guild_monthly_season(guild_id):
    init_guild_system_tables_only()

    current_season = get_current_guild_season_key()
    guild = get_guild_by_id(guild_id, ensure_season=False)

    if not guild:
        return False

    return archive_and_reset_guild_monthly_stats(guild, current_season)


def ensure_all_guild_monthly_seasons():
    init_guild_system_tables_only()

    current_season = get_current_guild_season_key()

    cursor.execute("SELECT * FROM guilds WHERE season_key != ?", (current_season,))
    rows = cursor.fetchall()

    for row in rows:
        archive_and_reset_guild_monthly_stats(row, current_season)

    return len(rows)


def init_guild_system_tables_only():
    """
    Легка перевірка, щоб helper-и могли викликатись після першої ініціалізації
    без рекурсії init_guild_system() -> ensure -> init.
    """

    # Нічого не робимо: таблиці створюються через init_guild_system().
    # Функція залишена як явний marker для безпечних викликів.
    return True


# ==============================
# ✅ GUILD CRUD
# ==============================

def add_guild_log(guild_id, event_type, text):
    cursor.execute("""
    INSERT INTO guild_logs (guild_id, event_type, text, created_at)
    VALUES (?, ?, ?, ?)
    """, (
        guild_id,
        event_type,
        text,
        now_iso(),
    ))

    conn.commit()


def get_guild_by_id(guild_id, ensure_season=True):
    cursor.execute("SELECT * FROM guilds WHERE id=?", (guild_id,))
    row = cursor.fetchone()

    if row and ensure_season:
        if row["season_key"] != get_current_guild_season_key():
            ensure_guild_monthly_season(guild_id)
            cursor.execute("SELECT * FROM guilds WHERE id=?", (guild_id,))
            row = cursor.fetchone()

    return row


def get_guild_by_name_or_tag(value):
    name_norm = normalize_guild_name(value)
    tag_norm = normalize_guild_tag(value)

    cursor.execute("""
    SELECT * FROM guilds
    WHERE name_norm=? OR tag_norm=?
    """, (
        name_norm,
        tag_norm,
    ))

    return cursor.fetchone()


def is_user_in_guild(user_id):
    cursor.execute("SELECT 1 FROM guild_members WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None


def get_user_guild_member(user_id):
    cursor.execute("SELECT * FROM guild_members WHERE user_id=?", (user_id,))
    return cursor.fetchone()


def get_user_guild(user_id):
    member = get_user_guild_member(user_id)

    if not member:
        return None

    return get_guild_by_id(member["guild_id"])


def get_user_guild_role(user_id):
    member = get_user_guild_member(user_id)

    if not member:
        return None

    return member["role"]


def validate_guild_create_input(name, tag, icon="🏰"):
    name = (name or "").strip()
    tag = normalize_guild_tag(tag)
    icon = (icon or "🏰").strip() or "🏰"

    if len(name) < 3:
        return {
            "success": False,
            "message": "❌ Назва гільдії має містити мінімум 3 символи."
        }

    if len(name) > 32:
        return {
            "success": False,
            "message": "❌ Назва гільдії має бути не довша за 32 символи."
        }

    if len(tag) < 2:
        return {
            "success": False,
            "message": "❌ Абревіатура гільдії має містити мінімум 2 символи."
        }

    if len(tag) > 5:
        return {
            "success": False,
            "message": "❌ Абревіатура гільдії має бути не довша за 5 символів."
        }

    existing = get_guild_by_name_or_tag(name)

    if existing:
        return {
            "success": False,
            "message": "❌ Гільдія з такою назвою або абревіатурою вже існує."
        }

    existing_tag = get_guild_by_name_or_tag(tag)

    if existing_tag:
        return {
            "success": False,
            "message": "❌ Гільдія з такою назвою або абревіатурою вже існує."
        }

    return {
        "success": True,
        "name": name,
        "tag": tag,
        "icon": icon,
    }


def create_guild(user_id, name, tag, icon="🏰"):
    """
    Створює гільдію.

    На 7.0.1 створення безкоштовне.
    Вартість можна додати пізніше через GUILD_CREATE_COST_GOLD.
    """

    init_guild_system()

    if is_user_in_guild(user_id):
        return {
            "success": False,
            "message": "❌ Ти вже перебуваєш у гільдії."
        }

    validation = validate_guild_create_input(name, tag, icon)

    if not validation.get("success"):
        return validation

    now = now_iso()
    season_key = get_current_guild_season_key()

    cursor.execute("""
    INSERT INTO guilds (
        name,
        name_norm,
        tag,
        tag_norm,
        icon,
        leader_user_id,
        level,
        exp,
        resource,
        member_limit,
        created_at,
        updated_at,
        season_key
    ) VALUES (?, ?, ?, ?, ?, ?, 1, 0, 0, ?, ?, ?, ?)
    """, (
        validation["name"],
        normalize_guild_name(validation["name"]),
        validation["tag"],
        normalize_guild_tag(validation["tag"]),
        validation["icon"],
        user_id,
        DEFAULT_GUILD_MEMBER_LIMIT,
        now,
        now,
        season_key,
    ))

    guild_id = cursor.lastrowid

    cursor.execute("""
    INSERT INTO guild_members (
        guild_id,
        user_id,
        role,
        joined_at
    ) VALUES (?, ?, ?, ?)
    """, (
        guild_id,
        user_id,
        GUILD_ROLE_LEADER,
        now,
    ))

    conn.commit()

    add_guild_log(
        guild_id=guild_id,
        event_type="guild_created",
        text=f"Гільдію {validation['icon']} [{validation['tag']}] {validation['name']} створено."
    )

    return {
        "success": True,
        "guild_id": guild_id,
        "message": f"✅ Гільдію {validation['icon']} [{validation['tag']}] {validation['name']} створено."
    }


# ==============================
# ✅ MEMBERS
# ==============================

def get_guild_members(guild_id):
    ensure_guild_monthly_season(guild_id)

    cursor.execute("""
    SELECT gm.*,
           users.character_name,
           users.level
    FROM guild_members gm
    LEFT JOIN users ON users.user_id = gm.user_id
    WHERE gm.guild_id=?
    ORDER BY
        CASE gm.role
            WHEN 'leader' THEN 1
            WHEN 'officer' THEN 2
            ELSE 3
        END,
        gm.contribution_score DESC,
        gm.joined_at ASC
    """, (
        guild_id,
    ))

    return cursor.fetchall()


def get_guild_member_count(guild_id):
    cursor.execute("SELECT COUNT(*) AS cnt FROM guild_members WHERE guild_id=?", (guild_id,))
    row = cursor.fetchone()
    return int(row["cnt"] if row else 0)


def can_manage_guild_applications(user_id, guild_id):
    member = get_user_guild_member(user_id)

    if not member:
        return False

    if int(member["guild_id"]) != int(guild_id):
        return False

    return member["role"] in [GUILD_ROLE_LEADER, GUILD_ROLE_OFFICER]


# ==============================
# ✅ APPLICATIONS CORE
# ==============================

def create_guild_application(user_id, guild_id):
    init_guild_system()

    if is_user_in_guild(user_id):
        return {
            "success": False,
            "message": "❌ Ти вже перебуваєш у гільдії."
        }

    guild = get_guild_by_id(guild_id)

    if not guild:
        return {
            "success": False,
            "message": "❌ Гільдію не знайдено."
        }

    cursor.execute("""
    SELECT * FROM guild_applications
    WHERE guild_id=? AND user_id=? AND status=?
    """, (
        guild_id,
        user_id,
        GUILD_APPLICATION_PENDING,
    ))

    if cursor.fetchone():
        return {
            "success": False,
            "message": "ℹ️ Ти вже подав заявку в цю гільдію."
        }

    cursor.execute("""
    INSERT INTO guild_applications (guild_id, user_id, status, created_at)
    VALUES (?, ?, ?, ?)
    """, (
        guild_id,
        user_id,
        GUILD_APPLICATION_PENDING,
        now_iso(),
    ))

    conn.commit()

    add_guild_log(
        guild_id=guild_id,
        event_type="application_created",
        text=f"Нова заявка до гільдії від user_id={user_id}."
    )

    return {
        "success": True,
        "message": "✅ Заявку до гільдії подано."
    }


def get_guild_applications(guild_id, status=GUILD_APPLICATION_PENDING):
    cursor.execute("""
    SELECT ga.*,
           users.character_name,
           users.level
    FROM guild_applications ga
    LEFT JOIN users ON users.user_id = ga.user_id
    WHERE ga.guild_id=? AND ga.status=?
    ORDER BY ga.created_at ASC
    """, (
        guild_id,
        status,
    ))

    return cursor.fetchall()


# ==============================
# ✅ PROGRESS / SCORE
# ==============================

def add_guild_progress(guild_id, exp=0, resource=0, kills=0, contracts=0, user_id=None, reason=""):
    """
    Додає прогрес гільдії одночасно в monthly і total counters.
    Також оновлює contribution учасника, якщо передано user_id.
    """

    init_guild_system()
    ensure_guild_monthly_season(guild_id)

    exp = int(exp or 0)
    resource = int(resource or 0)
    kills = int(kills or 0)
    contracts = int(contracts or 0)
    score = calculate_guild_score(exp, resource, kills, contracts)

    if exp == 0 and resource == 0 and kills == 0 and contracts == 0:
        return {
            "success": True,
            "message": "ℹ️ Немає прогресу для додавання."
        }

    cursor.execute("""
    UPDATE guilds
    SET exp = exp + ?,
        resource = resource + ?,
        monthly_exp = monthly_exp + ?,
        monthly_resource = monthly_resource + ?,
        monthly_kills = monthly_kills + ?,
        monthly_contracts = monthly_contracts + ?,
        monthly_score = monthly_score + ?,
        total_exp = total_exp + ?,
        total_resource = total_resource + ?,
        total_kills = total_kills + ?,
        total_contracts = total_contracts + ?,
        total_score = total_score + ?,
        updated_at=?
    WHERE id=?
    """, (
        exp,
        resource,
        exp,
        resource,
        kills,
        contracts,
        score,
        exp,
        resource,
        kills,
        contracts,
        score,
        now_iso(),
        guild_id,
    ))

    if user_id is not None:
        cursor.execute("""
        UPDATE guild_members
        SET contribution_exp = contribution_exp + ?,
            contribution_resource = contribution_resource + ?,
            contribution_kills = contribution_kills + ?,
            contribution_contracts = contribution_contracts + ?,
            contribution_score = contribution_score + ?,
            monthly_contribution_exp = monthly_contribution_exp + ?,
            monthly_contribution_resource = monthly_contribution_resource + ?,
            monthly_contribution_kills = monthly_contribution_kills + ?,
            monthly_contribution_contracts = monthly_contribution_contracts + ?,
            monthly_contribution_score = monthly_contribution_score + ?
        WHERE guild_id=? AND user_id=?
        """, (
            exp,
            resource,
            kills,
            contracts,
            score,
            exp,
            resource,
            kills,
            contracts,
            score,
            guild_id,
            user_id,
        ))

    conn.commit()

    if reason:
        add_guild_log(
            guild_id=guild_id,
            event_type="progress",
            text=reason,
        )

    return {
        "success": True,
        "exp": exp,
        "resource": resource,
        "kills": kills,
        "contracts": contracts,
        "score": score,
        "message": "✅ Прогрес гільдії оновлено."
    }


# ==============================
# ✅ RANKINGS
# ==============================

def get_guild_ranking(scope="monthly", limit=10):
    """
    Рейтинг гільдій.

    scope="monthly": поточний місячний рейтинг.
    scope="total": рейтинг за весь час.

    Сортування завжди від більшого до меншого.
    """

    init_guild_system()
    ensure_all_guild_monthly_seasons()

    try:
        limit = int(limit)
    except Exception:
        limit = 10

    limit = max(1, min(100, limit))

    if scope == "total":
        cursor.execute("""
        SELECT *
        FROM guilds
        ORDER BY total_score DESC,
                 total_exp DESC,
                 level DESC,
                 created_at ASC
        LIMIT ?
        """, (
            limit,
        ))
    else:
        cursor.execute("""
        SELECT *
        FROM guilds
        ORDER BY monthly_score DESC,
                 monthly_exp DESC,
                 total_score DESC,
                 created_at ASC
        LIMIT ?
        """, (
            limit,
        ))

    return cursor.fetchall()


def get_guild_season_history(guild_id=None, season_key=None, limit=20):
    init_guild_system()

    try:
        limit = int(limit)
    except Exception:
        limit = 20

    limit = max(1, min(100, limit))

    query = "SELECT * FROM guild_season_history WHERE 1=1"
    params = []

    if guild_id is not None:
        query += " AND guild_id=?"
        params.append(guild_id)

    if season_key is not None:
        query += " AND season_key=?"
        params.append(season_key)

    query += " ORDER BY season_key DESC, monthly_score DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    return cursor.fetchall()


# ==============================
# ✅ DISPLAY HELPERS
# ==============================

def get_guild_display_name(guild):
    if not guild:
        return "Без гільдії"

    icon = guild["icon"] or "🏰"
    tag = guild["tag"] or "???"
    name = guild["name"] or "Гільдія"

    return f"{icon} [{tag}] {name}"


def get_guild_role_label(role):
    if role == GUILD_ROLE_LEADER:
        return "👑 Голова"
    if role == GUILD_ROLE_OFFICER:
        return "🛡 Заступник"
    return "👤 Учасник"
