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



GUILD_CREATE_COST_GOLD = 100.0
DEFAULT_GUILD_MEMBER_LIMIT = 10
MIN_GUILD_ACCESS_LEVEL = 3


def get_guild_access_level_state(user_id):
    """Повертає canonical перевірку мінімального рівня для створення/вступу."""
    init_guild_system()
    row = cursor.execute("SELECT COALESCE(level, 0) FROM users WHERE user_id=?", (int(user_id),)).fetchone()
    level = int(row[0] if row else 0)
    return {
        "success": level >= MIN_GUILD_ACCESS_LEVEL,
        "level": level,
        "min_level": MIN_GUILD_ACCESS_LEVEL,
        "message": "" if level >= MIN_GUILD_ACCESS_LEVEL else (
            f"❌ Створення гільдії та вступ до гільдії доступні з {MIN_GUILD_ACCESS_LEVEL} рівня.\n"
            f"Твій поточний рівень: {level}."
        ),
    }
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


GUILD_NAME_LATIN_LETTERS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
GUILD_NAME_UKRAINIAN_LETTERS = frozenset("АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯабвгґдеєжзиіїйклмнопрстуфхцчшщьюя")
GUILD_NAME_APOSTROPHES = frozenset(("'", "’", "ʼ"))
_GUILD_EMOJI_VARIATION_SELECTORS = frozenset((0xFE0E, 0xFE0F))
_GUILD_EMOJI_ZWJ = 0x200D
_GUILD_EMOJI_KEYCAP = 0x20E3


def normalize_guild_name(value):
    import unicodedata
    return unicodedata.normalize("NFC", str(value or "").strip())


def normalize_guild_name_key(value):
    return normalize_guild_name(value).casefold()


def validate_guild_name_contract(value):
    name = normalize_guild_name(value)
    if len(name) < 3:
        return {"success": False, "message": "❌ Назва гільдії має містити мінімум 3 символи."}
    if len(name) > 32:
        return {"success": False, "message": "❌ Назва гільдії має бути не довша за 32 символи."}
    allowed = GUILD_NAME_LATIN_LETTERS | GUILD_NAME_UKRAINIAN_LETTERS | GUILD_NAME_APOSTROPHES | {"-", " "}
    if any(character not in allowed for character in name):
        return {"success": False, "message": "❌ Дозволені лише українські або латинські літери, одинарні пробіли, апостроф і дефіс. Цифри та emoji заборонені."}
    has_latin = any(character in GUILD_NAME_LATIN_LETTERS for character in name)
    has_ukrainian = any(character in GUILD_NAME_UKRAINIAN_LETTERS for character in name)
    if has_latin and has_ukrainian:
        return {"success": False, "message": "❌ Не змішуй українські та латинські літери в одній назві."}
    if "  " in name or "--" in name or name.startswith("-") or name.endswith("-"):
        return {"success": False, "message": "❌ Використовуй лише одинарні пробіли й дефіси між частинами назви."}
    return {"success": True, "name": name}


def _guild_is_regional_indicator(codepoint):
    return 0x1F1E6 <= codepoint <= 0x1F1FF


def _guild_is_emoji_modifier(codepoint):
    return 0x1F3FB <= codepoint <= 0x1F3FF


def _guild_is_emoji_base(codepoint):
    return (
        0x1F000 <= codepoint <= 0x1FAFF
        or 0x2600 <= codepoint <= 0x27BF
        or 0x2300 <= codepoint <= 0x23FF
        or codepoint in {0x00A9, 0x00AE, 0x203C, 0x2049, 0x2122, 0x2139, 0x3030, 0x303D, 0x3297, 0x3299}
    )


def _guild_consume_emoji_component(codepoints, index):
    if index >= len(codepoints) or not _guild_is_emoji_base(codepoints[index]):
        return None
    index += 1
    while index < len(codepoints) and (
        codepoints[index] in _GUILD_EMOJI_VARIATION_SELECTORS
        or _guild_is_emoji_modifier(codepoints[index])
    ):
        index += 1
    return index


def is_single_guild_emoji(value):
    import unicodedata
    text = unicodedata.normalize("NFC", str(value or "").strip())
    codepoints = [ord(character) for character in text]
    if not codepoints:
        return False
    if len(codepoints) == 2 and all(_guild_is_regional_indicator(cp) for cp in codepoints):
        return True
    if len(codepoints) in (2, 3) and codepoints[-1] == _GUILD_EMOJI_KEYCAP and chr(codepoints[0]) in "#*0123456789":
        return len(codepoints) == 2 or codepoints[1] in _GUILD_EMOJI_VARIATION_SELECTORS
    index = _guild_consume_emoji_component(codepoints, 0)
    if index is None:
        return False
    while index < len(codepoints):
        if codepoints[index] != _GUILD_EMOJI_ZWJ:
            return False
        index = _guild_consume_emoji_component(codepoints, index + 1)
        if index is None:
            return False
    return True


def validate_guild_icon_contract(value):
    icon = normalize_guild_icon(value)
    if not is_single_guild_emoji(icon):
        return {"success": False, "message": "❌ Іконка гільдії має містити рівно один emoji."}
    return {"success": True, "icon": icon}



GUILD_TAG_LATIN_LETTERS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
GUILD_TAG_UKRAINIAN_LETTERS = frozenset("АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ")
GUILD_TAG_ALLOWED_LETTERS = GUILD_TAG_LATIN_LETTERS | GUILD_TAG_UKRAINIAN_LETTERS


def normalize_guild_tag(value):
    return (value or "").strip().upper()


def validate_guild_tag_contract(value):
    tag = normalize_guild_tag(value)
    if len(tag) != 3:
        return {"success": False, "message": "❌ Абревіатура гільдії має складатися рівно з 3 літер."}
    if any(character not in GUILD_TAG_ALLOWED_LETTERS for character in tag):
        return {"success": False, "message": "❌ Дозволені лише українські та латинські літери."}
    return {"success": True, "tag": tag}



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


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guild_membership_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        guild_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        event_reason TEXT NOT NULL DEFAULT '',
        actor_user_id INTEGER,
        occurred_at TEXT NOT NULL,
        join_blocked_until TEXT NOT NULL
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_guild_membership_history_user_blocked ON guild_membership_history(user_id, join_blocked_until DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_guild_membership_history_guild_occurred ON guild_membership_history(guild_id, occurred_at DESC)")

    conn.commit()

    ensure_all_guild_monthly_seasons()
    # Stage 18.1.4b: enforce unique guild icons only after guild schema creation.
    make_existing_guild_icons_unique()
    ensure_unique_guild_icon_index()


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
    name_norm = normalize_guild_name_key(value)
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


# ROM 17.21.1 GUILD LEAVE COOLDOWN
from datetime import timezone as _guild_timezone_17_21_1, timedelta as _guild_timedelta_17_21_1

GUILD_LEAVE_COOLDOWN_HOURS = 24
_GUILD_EVENT_LEAVE_17_21_1 = "voluntary_leave"
_GUILD_EVENT_KICK_17_21_1 = "kicked"

def _guild_utc_now_17_21_1():
    return datetime.now(_guild_timezone_17_21_1.utc)

def _guild_utc_iso_17_21_1(value=None):
    value = value or _guild_utc_now_17_21_1()
    return value.astimezone(_guild_timezone_17_21_1.utc).isoformat()

def _guild_parse_utc_17_21_1(value):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_guild_timezone_17_21_1.utc)
    return parsed.astimezone(_guild_timezone_17_21_1.utc)

def _init_guild_membership_history_17_21_1(commit=True):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guild_membership_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        guild_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        event_reason TEXT NOT NULL DEFAULT '',
        actor_user_id INTEGER,
        occurred_at TEXT NOT NULL,
        join_blocked_until TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_guild_membership_history_user_blocked
    ON guild_membership_history(user_id, join_blocked_until DESC)
    """)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_guild_membership_history_guild_occurred
    ON guild_membership_history(guild_id, occurred_at DESC)
    """)
    if commit:
        conn.commit()
    return True

def get_guild_join_cooldown(user_id):
    _init_guild_membership_history_17_21_1(commit=False)
    row = cursor.execute("""
        SELECT guild_id, event_type, event_reason, actor_user_id,
               occurred_at, join_blocked_until
        FROM guild_membership_history
        WHERE user_id=?
        ORDER BY join_blocked_until DESC, id DESC
        LIMIT 1
    """, (int(user_id),)).fetchone()
    if not row:
        return {"active": False, "remaining_seconds": 0, "remaining_minutes": 0}
    blocked_until = _guild_parse_utc_17_21_1(row[5])
    now = _guild_utc_now_17_21_1()
    remaining = max(0, int((blocked_until - now).total_seconds())) if blocked_until else 0
    return {
        "active": remaining > 0,
        "remaining_seconds": remaining,
        "remaining_minutes": (remaining + 59) // 60 if remaining else 0,
        "guild_id": int(row[0]),
        "event_type": str(row[1]),
        "event_reason": str(row[2] or ""),
        "actor_user_id": row[3],
        "occurred_at": str(row[4]),
        "join_blocked_until": str(row[5]),
    }

def format_guild_join_cooldown_remaining(user_id):
    state = get_guild_join_cooldown(user_id)
    if not state.get("active"):
        return ""
    minutes = max(1, int(state.get("remaining_minutes") or 1))
    hours, minute_part = divmod(minutes, 60)
    if hours and minute_part:
        return f"{hours} год {minute_part} хв"
    if hours:
        return f"{hours} год"
    return f"{minute_part} хв"

def can_user_join_or_create_guild(user_id):
    state = get_guild_join_cooldown(user_id)
    if not state.get("active"):
        return {"success": True, "active": False, "message": ""}
    remaining = format_guild_join_cooldown_remaining(user_id)
    return {
        "success": False,
        "active": True,
        "remaining": remaining,
        "join_blocked_until": state.get("join_blocked_until"),
        "message": (
            "⏳ Вступ до гільдії тимчасово недоступний.\n"
            f"Залишилося: {remaining}."
        ),
    }

def _record_guild_departure_17_21_1(user_id, guild_id, event_type, reason="", actor_user_id=None):
    occurred = _guild_utc_now_17_21_1()
    blocked = occurred + _guild_timedelta_17_21_1(hours=GUILD_LEAVE_COOLDOWN_HOURS)
    cursor.execute("""
        INSERT INTO guild_membership_history (
            user_id, guild_id, event_type, event_reason, actor_user_id,
            occurred_at, join_blocked_until
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        int(user_id), int(guild_id), str(event_type), str(reason or ""),
        int(actor_user_id) if actor_user_id is not None else None,
        _guild_utc_iso_17_21_1(occurred), _guild_utc_iso_17_21_1(blocked),
    ))
    return _guild_utc_iso_17_21_1(blocked)

def create_guild(user_id, name, tag, icon="🏰"):
    """Атомарно створює гільдію за золото з базовим лімітом учасників."""
    init_guild_system()
    level_gate = get_guild_access_level_state(user_id)
    if not level_gate.get("success"):
        return level_gate
    user_id = int(user_id)
    validation = validate_guild_create_input(name, tag, icon)
    if not validation.get("success"):
        return validation
    savepoint = "paid_guild_creation_17_23_1"
    try:
        cursor.execute(f"SAVEPOINT {savepoint}")
        gate = can_user_join_or_create_guild(user_id)
        if not gate.get("success"):
            raise ValueError(gate.get("message") or "⏳ Створення гільдії тимчасово недоступне.")
        if is_user_in_guild(user_id):
            raise ValueError("❌ Ти вже перебуваєш у гільдії.")
        # Revalidate uniqueness inside the same transaction.
        validation = validate_guild_create_input(validation["name"], validation["tag"], validation["icon"])
        if not validation.get("success"):
            raise ValueError(validation.get("message") or "❌ Дані гільдії більше не доступні.")
        cursor.execute("UPDATE users SET gold=ROUND(gold-?, 2) WHERE user_id=? AND gold>=?", (GUILD_CREATE_COST_GOLD, user_id, GUILD_CREATE_COST_GOLD))
        if cursor.rowcount != 1:
            row = cursor.execute("SELECT COALESCE(gold,0) FROM users WHERE user_id=?", (user_id,)).fetchone()
            balance = float(row[0] if row else 0.0)
            raise ValueError(f"❌ Недостатньо золота. Потрібно: {GUILD_CREATE_COST_GOLD:.2f} 🪙. Твій баланс: {balance:.2f} 🪙.")
        now = now_iso(); season_key = get_current_guild_season_key()
        cursor.execute("""INSERT INTO guilds (name,name_norm,tag,tag_norm,icon,leader_user_id,level,exp,resource,member_limit,created_at,updated_at,season_key) VALUES (?,?,?,?,?,?,1,0,0,?,?,?,?)""", (validation["name"],normalize_guild_name_key(validation["name"]),validation["tag"],normalize_guild_tag(validation["tag"]),validation["icon"],user_id,DEFAULT_GUILD_MEMBER_LIMIT,now,now,season_key))
        guild_id = int(cursor.lastrowid)
        cursor.execute("INSERT INTO guild_members (guild_id,user_id,role,joined_at) VALUES (?,?,?,?)", (guild_id,user_id,GUILD_ROLE_LEADER,now))
        cursor.execute("INSERT INTO guild_logs (guild_id,event_type,text,created_at) VALUES (?,?,?,?)", (guild_id,"guild_created",f"Гільдію {validation['icon']} [{validation['tag']}] {validation['name']} створено за {GUILD_CREATE_COST_GOLD:.2f} золота.",now))
        row = cursor.execute("SELECT COALESCE(gold,0) FROM users WHERE user_id=?", (user_id,)).fetchone(); balance=float(row[0] if row else 0.0)
        cursor.execute(f"RELEASE {savepoint}"); conn.commit()
        return {"success":True,"guild_id":guild_id,"cost_gold":GUILD_CREATE_COST_GOLD,"gold_balance":balance,"member_limit":DEFAULT_GUILD_MEMBER_LIMIT,"message":f"✅ Гільдію {validation['icon']} [{validation['tag']}] {validation['name']} створено за {GUILD_CREATE_COST_GOLD:.2f} 🪙.\nЗалишок: {balance:.2f} 🪙."}
    except ValueError as error:
        try: cursor.execute(f"ROLLBACK TO {savepoint}"); cursor.execute(f"RELEASE {savepoint}")
        except Exception: conn.rollback()
        return {"success":False,"message":str(error),"cost_gold":GUILD_CREATE_COST_GOLD}
    except Exception as error:
        try: cursor.execute(f"ROLLBACK TO {savepoint}"); cursor.execute(f"RELEASE {savepoint}")
        except Exception: conn.rollback()
        return {"success":False,"message":f"❌ Не вдалося створити гільдію: {error}","cost_gold":GUILD_CREATE_COST_GOLD}


def get_guild_creation_terms(user_id):
    init_guild_system()
    row = cursor.execute("SELECT COALESCE(gold,0) FROM users WHERE user_id=?", (int(user_id),)).fetchone()
    balance = float(row[0] if row else 0.0)
    level_gate = get_guild_access_level_state(user_id)
    return {
        "cost_gold": float(GUILD_CREATE_COST_GOLD),
        "gold_balance": balance,
        "member_limit": int(DEFAULT_GUILD_MEMBER_LIMIT),
        "can_afford": balance >= float(GUILD_CREATE_COST_GOLD),
        "level": level_gate["level"],
        "min_level": level_gate["min_level"],
        "level_allowed": level_gate["success"],
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


# ==============================
# ✅ GUILD LIST APPLICATIONS CORE V1
# ==============================

# 7.0.4
# Список гільдій, перегляд деталей, подача заявки, перегляд моїх заявок.


def get_public_guild_list(limit=50, offset=0):
    """
    Публічний список гільдій.
    Сортування від більшого до меншого за total_score, далі level, далі дата створення.
    """

    init_guild_system()
    ensure_all_guild_monthly_seasons()

    try:
        limit = int(limit)
    except Exception:
        limit = 50

    try:
        offset = int(offset)
    except Exception:
        offset = 0

    limit = max(1, min(100, limit))
    offset = max(0, offset)

    cursor.execute("""
    SELECT g.*,
           COUNT(gm.user_id) AS member_count
    FROM guilds g
    LEFT JOIN guild_members gm ON gm.guild_id = g.id
    GROUP BY g.id
    ORDER BY g.total_score DESC,
             g.level DESC,
             g.created_at ASC
    LIMIT ? OFFSET ?
    """, (
        limit,
        offset,
    ))

    return cursor.fetchall()


def get_user_guild_applications(user_id, status=None):
    """
    Повертає заявки користувача.
    Якщо status=None — усі заявки.
    """

    init_guild_system()

    if status is None:
        cursor.execute("""
        SELECT ga.*,
               g.name AS guild_name,
               g.tag AS guild_tag,
               g.icon AS guild_icon
        FROM guild_applications ga
        JOIN guilds g ON g.id = ga.guild_id
        WHERE ga.user_id=?
        ORDER BY ga.created_at DESC
        """, (
            user_id,
        ))
    else:
        cursor.execute("""
        SELECT ga.*,
               g.name AS guild_name,
               g.tag AS guild_tag,
               g.icon AS guild_icon
        FROM guild_applications ga
        JOIN guilds g ON g.id = ga.guild_id
        WHERE ga.user_id=? AND ga.status=?
        ORDER BY ga.created_at DESC
        """, (
            user_id,
            status,
        ))

    return cursor.fetchall()


def has_pending_guild_application(user_id, guild_id):
    cursor.execute("""
    SELECT 1
    FROM guild_applications
    WHERE user_id=? AND guild_id=? AND status=?
    """, (
        user_id,
        guild_id,
        GUILD_APPLICATION_PENDING,
    ))

    return cursor.fetchone() is not None


def cancel_guild_application(user_id, application_id):
    """
    Скасовує pending заявку користувача.
    Буде корисно для UI пізніше.
    """

    init_guild_system()

    cursor.execute("""
    SELECT *
    FROM guild_applications
    WHERE id=? AND user_id=? AND status=?
    """, (
        application_id,
        user_id,
        GUILD_APPLICATION_PENDING,
    ))

    app = cursor.fetchone()

    if not app:
        return {
            "success": False,
            "message": "❌ Активну заявку не знайдено."
        }

    cursor.execute("""
    UPDATE guild_applications
    SET status=?, processed_at=?, processed_by=?
    WHERE id=?
    """, (
        GUILD_APPLICATION_CANCELLED,
        now_iso(),
        user_id,
        application_id,
    ))

    conn.commit()

    try:
        add_guild_log(
            guild_id=app["guild_id"],
            event_type="application_cancelled",
            text=f"Заявку user_id={user_id} скасовано."
        )
    except Exception:
        pass

    return {
        "success": True,
        "message": "✅ Заявку скасовано."
    }


# ==============================
# ✅ UNIQUE GUILD ICON CORE V1
# ==============================

# 7.0.4a
# Іконка гільдії має бути унікальною.
# Якщо в БД вже є дублікати, перша гільдія залишає іконку,
# інші дублікати отримують резервні унікальні іконки.

GUILD_RESERVED_UNIQUE_ICONS = [
    "🏰", "🛡️", "⚔️", "🔥", "🌙", "⭐", "🐺", "🐉", "🍀", "💎",
    "🦅", "🦁", "🐻", "🦊", "🦂", "🦉", "🗡️", "🔱", "🌲", "🌋",
    "❄️", "⚡", "🌟", "🌹", "🍒", "🌊", "☀️", "🌌", "🪓", "🧿",
]


def normalize_guild_icon(value):
    icon = (value or "").strip()
    return icon or "🏰"


def get_guild_by_icon(icon):
    init_guild_system_tables_only()
    icon = normalize_guild_icon(icon)

    cursor.execute("SELECT * FROM guilds WHERE icon=?", (icon,))
    return cursor.fetchone()


def is_guild_icon_taken(icon, exclude_guild_id=None):
    init_guild_system_tables_only()
    icon = normalize_guild_icon(icon)

    if exclude_guild_id is None:
        cursor.execute("SELECT 1 FROM guilds WHERE icon=?", (icon,))
    else:
        cursor.execute("SELECT 1 FROM guilds WHERE icon=? AND id != ?", (icon, exclude_guild_id))

    return cursor.fetchone() is not None


def _get_used_guild_icons():
    cursor.execute("SELECT icon FROM guilds")
    rows = cursor.fetchall()
    used = set()

    for row in rows:
        try:
            icon = row["icon"]
        except Exception:
            icon = row[0]
        if icon:
            used.add(icon)

    return used


def _pick_unique_guild_icon(used_icons, preferred=None):
    preferred = normalize_guild_icon(preferred)

    if preferred and preferred not in used_icons:
        return preferred

    for icon in GUILD_RESERVED_UNIQUE_ICONS:
        if icon not in used_icons:
            return icon

    # Very rare fallback if all reserved icons are used.
    # SQLite UNIQUE only needs unique text; UI validation for new guilds still asks for short emoji.
    counter = 1
    while True:
        candidate = f"🏰{counter}"
        if candidate not in used_icons:
            return candidate
        counter += 1


def make_existing_guild_icons_unique():
    """
    Виправляє вже існуючі дублікати icon у guilds.

    Правило:
    - найстаріша/перша гільдія з конкретною іконкою зберігає її;
    - наступні дублікати отримують резервну унікальну іконку.
    """

    init_guild_system_tables_only()

    cursor.execute("SELECT id, icon, name, tag FROM guilds ORDER BY id ASC")
    rows = cursor.fetchall()

    seen = set()
    used = set()
    changes = []

    for row in rows:
        try:
            guild_id = row["id"]
            icon = normalize_guild_icon(row["icon"])
            name = row["name"]
            tag = row["tag"]
        except Exception:
            guild_id = row[0]
            icon = normalize_guild_icon(row[1])
            name = row[2] if len(row) > 2 else "Гільдія"
            tag = row[3] if len(row) > 3 else "???"

        if icon not in seen and icon not in used:
            seen.add(icon)
            used.add(icon)
            continue

        new_icon = _pick_unique_guild_icon(used)
        used.add(new_icon)

        cursor.execute("UPDATE guilds SET icon=?, updated_at=? WHERE id=?", (new_icon, now_iso(), guild_id))
        changes.append((guild_id, icon, new_icon, name, tag))

    conn.commit()

    for guild_id, old_icon, new_icon, name, tag in changes:
        try:
            add_guild_log(
                guild_id=guild_id,
                event_type="icon_auto_changed",
                text=f"Іконку гільдії [{tag}] {name} автоматично змінено з {old_icon} на {new_icon}, бо іконки гільдій мають бути унікальними."
            )
        except Exception:
            pass

    return changes


def ensure_unique_guild_icon_index():
    """
    Створює UNIQUE index для guilds.icon після очищення дублікатів.
    """

    init_guild_system_tables_only()
    make_existing_guild_icons_unique()

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_guilds_icon_unique ON guilds(icon)")
    conn.commit()

    return True


# Override validation from 7.0.1 with icon uniqueness check.
def validate_guild_create_input(name, tag, icon="🏰"):
    name_validation = validate_guild_name_contract(name)
    if not name_validation["success"]:
        return name_validation
    name = name_validation["name"]
    tag = normalize_guild_tag(tag)
    icon_validation = validate_guild_icon_contract(icon)
    if not icon_validation["success"]:
        return icon_validation
    icon = icon_validation["icon"]

    tag_validation = validate_guild_tag_contract(tag)
    if not tag_validation["success"]:
        return tag_validation
    tag = tag_validation["tag"]

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

    if is_guild_icon_taken(icon):
        return {
            "success": False,
            "message": "❌ Така іконка вже використовується іншою гільдією. Обери іншу іконку."
        }

    return {
        "success": True,
        "name": name,
        "tag": tag,
        "icon": icon,
    }




# Ensure uniqueness whenever module is loaded after the patch.


# ==============================
# ✅ GUILD APPLICATION REVIEW CORE V1
# ==============================

# 7.0.5
# Обробка заявок у гільдію: прийняти / відхилити.


def get_guild_application_by_id(application_id):
    init_guild_system()
    cursor.execute("SELECT * FROM guild_applications WHERE id=?", (application_id,))
    return cursor.fetchone()


def accept_guild_application(actor_user_id, application_id):
    """
    Приймає заявку до гільдії.
    Доступно тільки leader/officer цієї гільдії.
    """

    init_guild_system()

    app = get_guild_application_by_id(application_id)

    if not app:
        return {"success": False, "message": "❌ Заявку не знайдено."}

    if app["status"] != GUILD_APPLICATION_PENDING:
        return {"success": False, "message": "❌ Ця заявка вже не очікує розгляду."}

    guild_id = app["guild_id"]
    applicant_user_id = app["user_id"]

    if not can_manage_guild_applications(actor_user_id, guild_id):
        return {"success": False, "message": "❌ У тебе немає прав для обробки заявок."}

    guild = get_guild_by_id(guild_id)
    if not guild:
        return {"success": False, "message": "❌ Гільдію не знайдено."}

    if is_user_in_guild(applicant_user_id):
        cursor.execute("""
        UPDATE guild_applications
        SET status=?, processed_at=?, processed_by=?
        WHERE id=?
        """, (
            GUILD_APPLICATION_REJECTED,
            now_iso(),
            actor_user_id,
            application_id,
        ))
        conn.commit()
        return {"success": False, "message": "❌ Гравець уже перебуває в іншій гільдії. Заявку відхилено."}

    member_count = get_guild_member_count(guild_id)
    member_limit = int(guild["member_limit"] or DEFAULT_GUILD_MEMBER_LIMIT)

    if member_count >= member_limit:
        return {"success": False, "message": "❌ У гільдії немає вільних місць."}

    now = now_iso()

    cursor.execute("""
    INSERT INTO guild_members (guild_id, user_id, role, joined_at)
    VALUES (?, ?, ?, ?)
    """, (
        guild_id,
        applicant_user_id,
        GUILD_ROLE_MEMBER,
        now,
    ))

    cursor.execute("""
    UPDATE guild_applications
    SET status=?, processed_at=?, processed_by=?
    WHERE id=?
    """, (
        GUILD_APPLICATION_ACCEPTED,
        now,
        actor_user_id,
        application_id,
    ))

    # Інші pending-заявки цього гравця автоматично скасовуємо.
    cursor.execute("""
    UPDATE guild_applications
    SET status=?, processed_at=?, processed_by=?
    WHERE user_id=? AND status=? AND id != ?
    """, (
        GUILD_APPLICATION_CANCELLED,
        now,
        actor_user_id,
        applicant_user_id,
        GUILD_APPLICATION_PENDING,
        application_id,
    ))

    conn.commit()

    applicant_name = f"user_id={applicant_user_id}"
    try:
        cursor.execute("SELECT character_name FROM users WHERE user_id=?", (applicant_user_id,))
        row = cursor.fetchone()
        if row:
            try:
                applicant_name = row["character_name"] or applicant_name
            except Exception:
                applicant_name = row[0] or applicant_name
    except Exception:
        pass

    add_guild_log(
        guild_id=guild_id,
        event_type="application_accepted",
        text=f"{applicant_name} вступив до гільдії."
    )

    return {"success": True, "message": f"✅ {applicant_name} прийнято до гільдії."}


def reject_guild_application(actor_user_id, application_id):
    """
    Відхиляє заявку до гільдії.
    Доступно тільки leader/officer цієї гільдії.
    """

    init_guild_system()

    app = get_guild_application_by_id(application_id)

    if not app:
        return {"success": False, "message": "❌ Заявку не знайдено."}

    if app["status"] != GUILD_APPLICATION_PENDING:
        return {"success": False, "message": "❌ Ця заявка вже не очікує розгляду."}

    guild_id = app["guild_id"]
    applicant_user_id = app["user_id"]

    if not can_manage_guild_applications(actor_user_id, guild_id):
        return {"success": False, "message": "❌ У тебе немає прав для обробки заявок."}

    now = now_iso()

    cursor.execute("""
    UPDATE guild_applications
    SET status=?, processed_at=?, processed_by=?
    WHERE id=?
    """, (
        GUILD_APPLICATION_REJECTED,
        now,
        actor_user_id,
        application_id,
    ))

    conn.commit()

    applicant_name = f"user_id={applicant_user_id}"
    try:
        cursor.execute("SELECT character_name FROM users WHERE user_id=?", (applicant_user_id,))
        row = cursor.fetchone()
        if row:
            try:
                applicant_name = row["character_name"] or applicant_name
            except Exception:
                applicant_name = row[0] or applicant_name
    except Exception:
        pass

    add_guild_log(
        guild_id=guild_id,
        event_type="application_rejected",
        text=f"Заявку від {applicant_name} відхилено."
    )

    return {"success": True, "message": f"✅ Заявку від {applicant_name} відхилено."}


# ==============================
# ✅ GUILD MEMBERS ROLES CORE V1
# ==============================

# 7.0.6
# Керування учасниками гільдії:
# - призначити заступника
# - зняти заступника
# - виключити учасника


def get_guild_member(guild_id, user_id):
    init_guild_system()
    cursor.execute(
        "SELECT * FROM guild_members WHERE guild_id=? AND user_id=?",
        (guild_id, user_id)
    )
    return cursor.fetchone()


def get_character_name_by_user_id(user_id):
    try:
        cursor.execute("SELECT character_name FROM users WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return f"user_id={user_id}"
        try:
            return row["character_name"] or f"user_id={user_id}"
        except Exception:
            return row[0] or f"user_id={user_id}"
    except Exception:
        return f"user_id={user_id}"


def is_guild_leader(user_id, guild_id):
    member = get_guild_member(guild_id, user_id)
    return bool(member and member["role"] == GUILD_ROLE_LEADER)


def is_guild_officer(user_id, guild_id):
    member = get_guild_member(guild_id, user_id)
    return bool(member and member["role"] == GUILD_ROLE_OFFICER)


def promote_guild_member_to_officer(actor_user_id, target_user_id):
    """Призначити єдиного заступника. Дозволено тільки голові."""
    init_guild_system()
    actor=get_user_guild_member(actor_user_id); target=get_user_guild_member(target_user_id)
    if not actor: return {"success":False,"message":"❌ Ти не перебуваєш у гільдії."}
    if not target or int(target["guild_id"])!=int(actor["guild_id"]): return {"success":False,"message":"❌ Цей гравець не перебуває у твоїй гільдії."}
    gid=int(actor["guild_id"])
    if str(actor["role"])!=GUILD_ROLE_LEADER: return {"success":False,"message":"❌ Призначати заступника може тільки 👑 Голова."}
    if str(target["role"])==GUILD_ROLE_LEADER: return {"success":False,"message":"❌ Голова вже має найвищу роль."}
    if str(target["role"])==GUILD_ROLE_OFFICER: return {"success":False,"message":"ℹ️ Цей гравець уже є 🛡 Заступником."}
    officer=get_guild_officer_member(gid)
    if officer:
        name=get_character_name_by_user_id(officer["user_id"])
        return {"success":False,"message":f"❌ У гільдії вже є 🛡 Заступник: {name}. Спочатку зніми його з посади."}
    cursor.execute("UPDATE guild_members SET role=? WHERE guild_id=? AND user_id=? AND role=?",(GUILD_ROLE_OFFICER,gid,int(target_user_id),GUILD_ROLE_MEMBER))
    if cursor.rowcount!=1: conn.rollback(); return {"success":False,"message":"❌ Роль учасника змінилася. Операцію скасовано."}
    conn.commit(); name=get_character_name_by_user_id(target_user_id)
    add_guild_log(guild_id=gid,event_type="member_promoted",text=f"{name} призначений 🛡 Заступником.")
    return {"success":True,"message":f"✅ {name} тепер 🛡 Заступник гільдії."}


def demote_guild_officer(actor_user_id, target_user_id):
    """
    Зняти заступника до учасника.
    Дозволено тільки голові гільдії.
    """

    init_guild_system()
    actor_member = get_user_guild_member(actor_user_id)
    target_member = get_user_guild_member(target_user_id)

    if not actor_member:
        return {"success": False, "message": "❌ Ти не перебуваєш у гільдії."}

    if not target_member or int(target_member["guild_id"]) != int(actor_member["guild_id"]):
        return {"success": False, "message": "❌ Цей гравець не перебуває у твоїй гільдії."}

    guild_id = actor_member["guild_id"]

    if actor_member["role"] != GUILD_ROLE_LEADER:
        return {"success": False, "message": "❌ Знімати заступників може тільки 👑 Голова гільдії."}

    if target_member["role"] != GUILD_ROLE_OFFICER:
        return {"success": False, "message": "❌ Цей гравець не є заступником."}

    cursor.execute(
        "UPDATE guild_members SET role=? WHERE guild_id=? AND user_id=?",
        (GUILD_ROLE_MEMBER, guild_id, target_user_id)
    )
    conn.commit()

    target_name = get_character_name_by_user_id(target_user_id)
    add_guild_log(
        guild_id=guild_id,
        event_type="member_demoted",
        text=f"{target_name} більше не є 🛡 Заступником."
    )

    return {"success": True, "message": f"✅ {target_name} тепер 👤 Учасник гільдії."}


def kick_guild_member(actor_user_id, target_user_id):
    init_guild_system()
    actor_member = get_user_guild_member(actor_user_id)
    target_member = get_user_guild_member(target_user_id)
    if not actor_member:
        return {"success": False, "message": "❌ Ти не перебуваєш у гільдії."}
    if not target_member or int(target_member["guild_id"]) != int(actor_member["guild_id"]):
        return {"success": False, "message": "❌ Цей гравець не перебуває у твоїй гільдії."}
    guild_id = int(actor_member["guild_id"])
    if int(actor_user_id) == int(target_user_id):
        return {"success": False, "message": "❌ Не можна виключити самого себе."}
    if str(target_member["role"]) == GUILD_ROLE_LEADER:
        return {"success": False, "message": "❌ Голову гільдії не можна виключити."}
    if str(actor_member["role"]) == GUILD_ROLE_MEMBER:
        return {"success": False, "message": "❌ Учасник не може виключати інших учасників."}
    if str(actor_member["role"]) == GUILD_ROLE_OFFICER and str(target_member["role"]) != GUILD_ROLE_MEMBER:
        return {"success": False, "message": "❌ Заступник може виключати тільки звичайних учасників."}
    target_name = get_character_name_by_user_id(target_user_id)
    savepoint = "guild_kick_17_21_1"
    try:
        cursor.execute(f"SAVEPOINT {savepoint}")
        cursor.execute("DELETE FROM guild_members WHERE guild_id=? AND user_id=?", (guild_id, int(target_user_id)))
        if cursor.rowcount != 1:
            raise RuntimeError("guild membership delete did not affect exactly one row")
        cursor.execute("""
            UPDATE guild_applications
            SET status=?, processed_at=?, processed_by=?
            WHERE user_id=? AND status=?
        """, (GUILD_APPLICATION_CANCELLED, _guild_utc_iso_17_21_1(), int(actor_user_id), int(target_user_id), GUILD_APPLICATION_PENDING))
        blocked_until = _record_guild_departure_17_21_1(
            target_user_id, guild_id, _GUILD_EVENT_KICK_17_21_1,
            reason="kicked", actor_user_id=actor_user_id,
        )
        cursor.execute("""
            INSERT INTO guild_logs (guild_id, event_type, text, created_at)
            VALUES (?, ?, ?, ?)
        """, (guild_id, "member_kicked", f"Учасника виключено з гільдії: {target_name}.", _guild_utc_iso_17_21_1()))
        cursor.execute(f"RELEASE {savepoint}")
        conn.commit()
        return {
            "success": True, "join_blocked_until": blocked_until,
            "message": f"✅ {target_name} виключений з гільдії."
        }
    except Exception as error:
        try:
            cursor.execute(f"ROLLBACK TO {savepoint}")
            cursor.execute(f"RELEASE {savepoint}")
        except Exception:
            conn.rollback()
        return {"success": False, "message": f"❌ Не вдалося виключити учасника: {error}"}

def leave_guild(user_id):
    init_guild_system()
    member = get_user_guild_member(user_id)
    if not member:
        return {"success": False, "message": "❌ Ти не перебуваєш у гільдії."}
    guild_id = int(member["guild_id"])
    if str(member["role"]) == GUILD_ROLE_LEADER:
        return {
            "success": False,
            "leader_blocked": True,
            "message": "❌ Голова не може покинути гільдію без передачі керівництва."
        }
    actor_name = get_character_name_by_user_id(user_id)
    savepoint = "guild_leave_17_21_1"
    try:
        cursor.execute(f"SAVEPOINT {savepoint}")
        cursor.execute("DELETE FROM guild_members WHERE guild_id=? AND user_id=?", (guild_id, int(user_id)))
        if cursor.rowcount != 1:
            raise RuntimeError("guild membership delete did not affect exactly one row")
        cursor.execute("""
            UPDATE guild_applications
            SET status=?, processed_at=?, processed_by=?
            WHERE user_id=? AND status=?
        """, (GUILD_APPLICATION_CANCELLED, _guild_utc_iso_17_21_1(), int(user_id), int(user_id), GUILD_APPLICATION_PENDING))
        blocked_until = _record_guild_departure_17_21_1(
            user_id, guild_id, _GUILD_EVENT_LEAVE_17_21_1,
            reason="voluntary_leave", actor_user_id=user_id,
        )
        cursor.execute("""
            INSERT INTO guild_logs (guild_id, event_type, text, created_at)
            VALUES (?, ?, ?, ?)
        """, (guild_id, "member_left", f"Учасник покинув гільдію: {actor_name}.", _guild_utc_iso_17_21_1()))
        cursor.execute(f"RELEASE {savepoint}")
        conn.commit()
        return {
            "success": True,
            "guild_id": guild_id,
            "join_blocked_until": blocked_until,
            "message": (
                "✅ Ти покинув гільдію.\n\n"
                "⏳ Вступ до іншої гільдії та створення власної "
                "будуть недоступні протягом 24 годин."
            ),
        }
    except Exception as error:
        try:
            cursor.execute(f"ROLLBACK TO {savepoint}")
            cursor.execute(f"RELEASE {savepoint}")
        except Exception:
            conn.rollback()
        return {"success": False, "message": f"❌ Не вдалося покинути гільдію: {error}"}

# ROM 17.22.1 GUILD LEADERSHIP TRANSFER AND LEADER EXIT
def _validate_guild_leadership_transfer_17_22_1(actor_user_id, successor_user_id):
    actor_user_id=int(actor_user_id); successor_user_id=int(successor_user_id)
    if actor_user_id==successor_user_id: return None,None,{"success":False,"message":"❌ Не можна передати керівництво самому собі."}
    actor=get_user_guild_member(actor_user_id); successor=get_user_guild_member(successor_user_id)
    if not actor or str(actor["role"])!=GUILD_ROLE_LEADER: return None,None,{"success":False,"message":"❌ Передавати керівництво може тільки чинний голова."}
    gid=int(actor["guild_id"])
    if not successor or int(successor["guild_id"])!=gid: return None,None,{"success":False,"message":"❌ Обраний гравець не перебуває у твоїй гільдії."}
    guild=cursor.execute("SELECT leader_user_id FROM guilds WHERE id=?",(gid,)).fetchone()
    leaders=cursor.execute("SELECT user_id FROM guild_members WHERE guild_id=? AND role=?",(gid,GUILD_ROLE_LEADER)).fetchall()
    if not guild or int(guild[0])!=actor_user_id or len(leaders)!=1 or int(leaders[0][0])!=actor_user_id:
        return None,None,{"success":False,"data_inconsistent":True,"message":"❌ Дані керівництва гільдії неузгоджені. Передачу скасовано."}
    return actor,successor,None

def transfer_guild_leadership(actor_user_id, successor_user_id):
    """Атомарно передає керівництво; попередній голова стає заступником."""
    init_guild_system(); actor,successor,error=_validate_guild_leadership_transfer_17_22_1(actor_user_id,successor_user_id)
    if error: return error
    gid=int(actor["guild_id"]); actor_user_id=int(actor_user_id); successor_user_id=int(successor_user_id)
    old_name=get_character_name_by_user_id(actor_user_id); new_name=get_character_name_by_user_id(successor_user_id); sp='guild_transfer_17_22_1'
    try:
        cursor.execute(f"SAVEPOINT {sp}")
        cursor.execute("UPDATE guild_members SET role=? WHERE guild_id=? AND role=? AND user_id NOT IN (?,?)",(GUILD_ROLE_MEMBER,gid,GUILD_ROLE_OFFICER,actor_user_id,successor_user_id))
        cursor.execute("UPDATE guild_members SET role=? WHERE guild_id=? AND user_id=? AND role=?",(GUILD_ROLE_LEADER,gid,successor_user_id,str(successor["role"])))
        if cursor.rowcount!=1: raise RuntimeError('successor role changed')
        cursor.execute("UPDATE guild_members SET role=? WHERE guild_id=? AND user_id=? AND role=?",(GUILD_ROLE_OFFICER,gid,actor_user_id,GUILD_ROLE_LEADER))
        if cursor.rowcount!=1: raise RuntimeError('leader role changed')
        cursor.execute("UPDATE guilds SET leader_user_id=?,updated_at=? WHERE id=? AND leader_user_id=?",(successor_user_id,_guild_utc_iso_17_21_1(),gid,actor_user_id))
        if cursor.rowcount!=1: raise RuntimeError('guild leader changed')
        cursor.execute("INSERT INTO guild_logs(guild_id,event_type,text,created_at) VALUES(?,?,?,?)",(gid,'leadership_transferred',f"{old_name} передав керівництво гравцю {new_name}.",_guild_utc_iso_17_21_1()))
        cursor.execute(f"RELEASE {sp}"); conn.commit()
        return {"success":True,"guild_id":gid,"successor_user_id":successor_user_id,"message":f"✅ Керівництво передано гравцю {new_name}. Ти тепер 🛡 Заступник."}
    except Exception as e:
        try: cursor.execute(f"ROLLBACK TO {sp}"); cursor.execute(f"RELEASE {sp}")
        except Exception: conn.rollback()
        return {"success":False,"message":f"❌ Не вдалося передати керівництво: {e}"}

def transfer_guild_leadership_and_leave(actor_user_id, successor_user_id):
    """Атомарно передає керівництво, видаляє колишнього голову та вмикає cooldown."""
    init_guild_system(); actor,successor,error=_validate_guild_leadership_transfer_17_22_1(actor_user_id,successor_user_id)
    if error: return error
    gid=int(actor["guild_id"]); actor_user_id=int(actor_user_id); successor_user_id=int(successor_user_id)
    count=int(cursor.execute("SELECT COUNT(*) FROM guild_members WHERE guild_id=?",(gid,)).fetchone()[0] or 0)
    if count<=1: return {"success":False,"sole_member":True,"message":"❌ Голова не може покинути одноосібну гільдію."}
    old_name=get_character_name_by_user_id(actor_user_id); new_name=get_character_name_by_user_id(successor_user_id); sp='guild_leader_exit_17_22_1'
    try:
        cursor.execute(f"SAVEPOINT {sp}")
        cursor.execute("UPDATE guild_members SET role=? WHERE guild_id=? AND role=? AND user_id<>?",(GUILD_ROLE_MEMBER,gid,GUILD_ROLE_OFFICER,successor_user_id))
        cursor.execute("UPDATE guild_members SET role=? WHERE guild_id=? AND user_id=? AND role=?",(GUILD_ROLE_LEADER,gid,successor_user_id,str(successor["role"])))
        if cursor.rowcount!=1: raise RuntimeError('successor role changed')
        cursor.execute("UPDATE guilds SET leader_user_id=?,updated_at=? WHERE id=? AND leader_user_id=?",(successor_user_id,_guild_utc_iso_17_21_1(),gid,actor_user_id))
        if cursor.rowcount!=1: raise RuntimeError('guild leader changed')
        cursor.execute("DELETE FROM guild_members WHERE guild_id=? AND user_id=? AND role=?",(gid,actor_user_id,GUILD_ROLE_LEADER))
        if cursor.rowcount!=1: raise RuntimeError('former leader membership changed')
        cursor.execute("UPDATE guild_applications SET status=?,processed_at=?,processed_by=? WHERE user_id=? AND status=?",(GUILD_APPLICATION_CANCELLED,_guild_utc_iso_17_21_1(),actor_user_id,actor_user_id,GUILD_APPLICATION_PENDING))
        blocked=_record_guild_departure_17_21_1(actor_user_id,gid,_GUILD_EVENT_LEAVE_17_21_1,reason='leadership_transfer_leave',actor_user_id=actor_user_id)
        cursor.execute("INSERT INTO guild_logs(guild_id,event_type,text,created_at) VALUES(?,?,?,?)",(gid,'leadership_transferred_leader_left',f"{old_name} передав керівництво гравцю {new_name} і покинув гільдію.",_guild_utc_iso_17_21_1()))
        cursor.execute(f"RELEASE {sp}"); conn.commit()
        return {"success":True,"guild_id":gid,"successor_user_id":successor_user_id,"join_blocked_until":blocked,"message":f"✅ Керівництво передано гравцю {new_name}. Ти покинув гільдію.\n\n⏳ Вступ і створення гільдії недоступні 24 години."}
    except Exception as e:
        try: cursor.execute(f"ROLLBACK TO {sp}"); cursor.execute(f"RELEASE {sp}")
        except Exception: conn.rollback()
        return {"success":False,"message":f"❌ Не вдалося передати керівництво та вийти: {e}"}



# ==============================
# ✅ GUILD SINGLE OFFICER CORE V1
# ==============================

# 7.0.6a
# У гільдії може бути максимум один 🛡 Заступник.


def get_guild_officer_count(guild_id):
    init_guild_system()
    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM guild_members WHERE guild_id=? AND role=?",
        (guild_id, GUILD_ROLE_OFFICER)
    )
    row = cursor.fetchone()
    try:
        return int(row["cnt"] or 0)
    except Exception:
        return int(row[0] or 0) if row else 0


def get_guild_officer_member(guild_id):
    init_guild_system()
    cursor.execute(
        "SELECT * FROM guild_members WHERE guild_id=? AND role=? LIMIT 1",
        (guild_id, GUILD_ROLE_OFFICER)
    )
    return cursor.fetchone()


try:
    _base_promote_guild_member_to_officer_before_single_officer_v1 = promote_guild_member_to_officer
except Exception:
    _base_promote_guild_member_to_officer_before_single_officer_v1 = None




# ==============================
# ✅ GUILD ACCEPT APPLICATION IDEMPOTENT FIX V1
# ==============================

# 7.0.6b
# Fix проблеми:
# - гравець уже додався в guild_members;
# - заявка лишилась pending;
# - повторне натискання ✅ Прийняти заявку падало через UNIQUE constraint
#   guild_applications(guild_id, user_id, status).
#
# Рішення:
# - прийняття заявки стало idempotent;
# - якщо гравець уже в цій гільдії, pending-заявка просто позначається accepted/removes duplicate safely;
# - якщо already є accepted-заявка з таким UNIQUE ключем, pending-заявка видаляється;
# - старі pending-заявки гравця в інші гільдії скасовуються.


def _guild_safe_set_application_status(application_id, status, processed_by=None):
    """
    Безпечно змінює статус заявки з урахуванням UNIQUE(guild_id, user_id, status).

    Якщо запис із таким status уже існує, поточна заявка видаляється,
    щоб не ламати БД і не залишати pending-дублікат.
    """

    app = get_guild_application_by_id(application_id)
    if not app:
        return False

    now = now_iso()

    try:
        cursor.execute("""
        UPDATE guild_applications
        SET status=?, processed_at=?, processed_by=?
        WHERE id=?
        """, (
            status,
            now,
            processed_by,
            application_id,
        ))
        conn.commit()
        return True
    except Exception as error:
        if "UNIQUE constraint failed" not in str(error):
            raise

        # Є інша заявка з таким самим guild_id/user_id/status.
        # Поточний pending-запис більше не потрібен.
        cursor.execute("DELETE FROM guild_applications WHERE id=?", (application_id,))
        conn.commit()
        return True


def _guild_cancel_other_pending_applications(user_id, except_application_id=None, processed_by=None):
    now = now_iso()

    if except_application_id is None:
        cursor.execute("""
        UPDATE guild_applications
        SET status=?, processed_at=?, processed_by=?
        WHERE user_id=? AND status=?
        """, (
            GUILD_APPLICATION_CANCELLED,
            now,
            processed_by,
            user_id,
            GUILD_APPLICATION_PENDING,
        ))
    else:
        cursor.execute("""
        UPDATE guild_applications
        SET status=?, processed_at=?, processed_by=?
        WHERE user_id=? AND status=? AND id != ?
        """, (
            GUILD_APPLICATION_CANCELLED,
            now,
            processed_by,
            user_id,
            GUILD_APPLICATION_PENDING,
            except_application_id,
        ))

    conn.commit()


# FINAL OVERRIDE for 7.0.5 accept_guild_application.
def accept_guild_application(actor_user_id, application_id):
    init_guild_system()

    app = get_guild_application_by_id(application_id)

    if not app:
        return {"success": False, "message": "❌ Заявку не знайдено."}

    guild_id = app["guild_id"]
    applicant_user_id = app["user_id"]

    applicant_level_gate = get_guild_access_level_state(applicant_user_id)
    if not applicant_level_gate.get("success"):
        _guild_safe_set_application_status(
            application_id,
            GUILD_APPLICATION_REJECTED,
            processed_by=actor_user_id,
        )
        return {
            "success": False,
            "message": (
                f"❌ Заявку відхилено: вступ доступний з {MIN_GUILD_ACCESS_LEVEL} рівня. "
                f"Поточний рівень гравця: {applicant_level_gate.get('level', 0)}."
            ),
        }

    if app["status"] != GUILD_APPLICATION_PENDING:
        return {"success": False, "message": "❌ Ця заявка вже не очікує розгляду."}

    if not can_manage_guild_applications(actor_user_id, guild_id):
        return {"success": False, "message": "❌ У тебе немає прав для обробки заявок."}

    guild = get_guild_by_id(guild_id)
    if not guild:
        return {"success": False, "message": "❌ Гільдію не знайдено."}

    applicant_name = get_character_name_by_user_id(applicant_user_id)
    existing_member = get_user_guild_member(applicant_user_id)

    # Idempotent recovery: гравець уже в цій гільдії, але pending-заявка висить.
    if existing_member and int(existing_member["guild_id"]) == int(guild_id):
        _guild_safe_set_application_status(
            application_id,
            GUILD_APPLICATION_ACCEPTED,
            processed_by=actor_user_id,
        )
        _guild_cancel_other_pending_applications(
            applicant_user_id,
            except_application_id=application_id,
            processed_by=actor_user_id,
        )
        return {
            "success": True,
            "message": f"✅ {applicant_name} уже перебуває в цій гільдії. Заявку очищено."
        }

    # Якщо гравець уже в іншій гільдії — pending-заявку треба прибрати без падіння.
    if existing_member and int(existing_member["guild_id"]) != int(guild_id):
        _guild_safe_set_application_status(
            application_id,
            GUILD_APPLICATION_REJECTED,
            processed_by=actor_user_id,
        )
        return {"success": False, "message": "❌ Гравець уже перебуває в іншій гільдії. Заявку відхилено."}

    member_count = get_guild_member_count(guild_id)
    member_limit = int(guild["member_limit"] or DEFAULT_GUILD_MEMBER_LIMIT)

    if member_count >= member_limit:
        return {"success": False, "message": "❌ У гільдії немає вільних місць."}

    now = now_iso()

    try:
        cursor.execute("""
        INSERT INTO guild_members (guild_id, user_id, role, joined_at)
        VALUES (?, ?, ?, ?)
        """, (
            guild_id,
            applicant_user_id,
            GUILD_ROLE_MEMBER,
            now,
        ))
        conn.commit()
    except Exception as error:
        # Якщо паралельно/раніше гравець уже був доданий — переводимо в idempotent branch.
        if "UNIQUE constraint failed" not in str(error):
            raise

    _guild_safe_set_application_status(
        application_id,
        GUILD_APPLICATION_ACCEPTED,
        processed_by=actor_user_id,
    )

    _guild_cancel_other_pending_applications(
        applicant_user_id,
        except_application_id=application_id,
        processed_by=actor_user_id,
    )

    try:
        add_guild_log(
            guild_id=guild_id,
            event_type="application_accepted",
            text=f"{applicant_name} вступив до гільдії."
        )
    except Exception:
        pass

    return {"success": True, "message": f"✅ {applicant_name} прийнято до гільдії."}


def cleanup_stale_guild_applications():
    """
    Чистить старі pending-заявки від гравців, які вже є в тій самій гільдії.
    Також прибирає pending-заявки в інші гільдії для гравців, які вже десь перебувають.
    """

    init_guild_system()

    fixed_same_guild = 0
    cancelled_other_guild = 0

    cursor.execute("""
    SELECT ga.id, ga.guild_id, ga.user_id, gm.guild_id AS member_guild_id
    FROM guild_applications ga
    JOIN guild_members gm ON gm.user_id = ga.user_id
    WHERE ga.status=?
    """, (GUILD_APPLICATION_PENDING,))

    rows = cursor.fetchall()

    for row in rows:
        app_id = row["id"]
        app_guild_id = row["guild_id"]
        member_guild_id = row["member_guild_id"]

        if int(app_guild_id) == int(member_guild_id):
            _guild_safe_set_application_status(app_id, GUILD_APPLICATION_ACCEPTED, processed_by=None)
            fixed_same_guild += 1
        else:
            _guild_safe_set_application_status(app_id, GUILD_APPLICATION_CANCELLED, processed_by=None)
            cancelled_other_guild += 1

    return {
        "fixed_same_guild": fixed_same_guild,
        "cancelled_other_guild": cancelled_other_guild,
    }


# ==============================
# ✅ GUILD PROGRESS CONTRIBUTIONS CORE V1
# ==============================

# 7.0.7
# Guild EXP / Resource / внесок учасників.
# На цьому етапі додаємо:
# - рівень гільдії від загального EXP;
# - рейтинг внеску учасників;
# - helper-и для прогресу;
# - add_guild_progress() лишається центральною точкою нарахування.

GUILD_LEVEL_EXP_BASE = 1000


def get_guild_exp_required_for_level(level):
    """
    Скільки total EXP потрібно для конкретного рівня гільдії.

    Level 1: 0
    Level 2: 1000
    Level 3: 3000
    Level 4: 6000

    Формула накопичувальна: sum(base * n) для n=1..level-1.
    """

    try:
        level = int(level)
    except Exception:
        level = 1

    level = max(1, level)

    if level <= 1:
        return 0

    return int(GUILD_LEVEL_EXP_BASE * ((level - 1) * level / 2))


def calculate_guild_level_from_exp(total_exp):
    try:
        total_exp = int(total_exp or 0)
    except Exception:
        total_exp = 0

    level = 1

    while total_exp >= get_guild_exp_required_for_level(level + 1):
        level += 1

    return level


def get_guild_next_level_info(guild_id):
    guild = get_guild_by_id(guild_id)

    if not guild:
        return None

    total_exp = int(guild["total_exp"] or 0)
    level = int(guild["level"] or 1)
    calculated_level = calculate_guild_level_from_exp(total_exp)

    if calculated_level > level:
        level = calculated_level

    current_level_exp = get_guild_exp_required_for_level(level)
    next_level_exp = get_guild_exp_required_for_level(level + 1)
    progress_exp = max(0, total_exp - current_level_exp)
    needed_exp = max(1, next_level_exp - current_level_exp)
    progress_percent = min(100.0, max(0.0, progress_exp / needed_exp * 100))

    return {
        "level": level,
        "total_exp": total_exp,
        "current_level_exp": current_level_exp,
        "next_level_exp": next_level_exp,
        "progress_exp": progress_exp,
        "needed_exp": needed_exp,
        "progress_percent": progress_percent,
    }


def recalculate_guild_level(guild_id):
    guild = get_guild_by_id(guild_id)

    if not guild:
        return None

    old_level = int(guild["level"] or 1)
    total_exp = int(guild["total_exp"] or 0)
    new_level = calculate_guild_level_from_exp(total_exp)

    if new_level != old_level:
        cursor.execute(
            "UPDATE guilds SET level=?, updated_at=? WHERE id=?",
            (new_level, now_iso(), guild_id)
        )
        conn.commit()

        if new_level > old_level:
            try:
                add_guild_log(
                    guild_id=guild_id,
                    event_type="guild_level_up",
                    text=f"Гільдія піднялась до рівня {new_level}."
                )
            except Exception:
                pass

    return new_level


try:
    _base_add_guild_progress_before_contributions_v1 = add_guild_progress
except Exception:
    _base_add_guild_progress_before_contributions_v1 = None


def add_guild_progress(guild_id, exp=0, resource=0, kills=0, contracts=0, user_id=None, reason=""):
    """
    FINAL OVERRIDE:
    Додає прогрес через базову функцію 7.0.1 і після цього перераховує рівень гільдії.
    """

    if _base_add_guild_progress_before_contributions_v1 is None:
        return {
            "success": False,
            "message": "❌ Базова функція add_guild_progress недоступна."
        }

    result = _base_add_guild_progress_before_contributions_v1(
        guild_id=guild_id,
        exp=exp,
        resource=resource,
        kills=kills,
        contracts=contracts,
        user_id=user_id,
        reason=reason,
    )

    try:
        result["guild_level"] = recalculate_guild_level(guild_id)
        result["next_level_info"] = get_guild_next_level_info(guild_id)
    except Exception:
        pass

    return result


def add_user_guild_progress(user_id, exp=0, resource=0, kills=0, contracts=0, reason=""):
    """
    Додає прогрес гільдії від конкретного учасника.
    Саме цю функцію варто використовувати для майбутньої інтеграції з контрактами/елітними мобами.
    """

    member = get_user_guild_member(user_id)

    if not member:
        return {
            "success": False,
            "message": "❌ Гравець не перебуває у гільдії."
        }

    return add_guild_progress(
        guild_id=member["guild_id"],
        exp=exp,
        resource=resource,
        kills=kills,
        contracts=contracts,
        user_id=user_id,
        reason=reason,
    )


def get_guild_contribution_ranking(guild_id, scope="monthly", limit=30):
    init_guild_system()
    ensure_guild_monthly_season(guild_id)

    try:
        limit = int(limit)
    except Exception:
        limit = 30

    limit = max(1, min(100, limit))

    if scope == "total":
        cursor.execute("""
        SELECT gm.*,
               users.character_name,
               users.level
        FROM guild_members gm
        LEFT JOIN users ON users.user_id = gm.user_id
        WHERE gm.guild_id=?
        ORDER BY gm.contribution_score DESC,
                 gm.contribution_exp DESC,
                 gm.joined_at ASC
        LIMIT ?
        """, (guild_id, limit))
    else:
        cursor.execute("""
        SELECT gm.*,
               users.character_name,
               users.level
        FROM guild_members gm
        LEFT JOIN users ON users.user_id = gm.user_id
        WHERE gm.guild_id=?
        ORDER BY gm.monthly_contribution_score DESC,
                 gm.monthly_contribution_exp DESC,
                 gm.joined_at ASC
        LIMIT ?
        """, (guild_id, limit))

    return cursor.fetchall()


def cleanup_recalculate_all_guild_levels():
    init_guild_system()
    cursor.execute("SELECT id FROM guilds")
    rows = cursor.fetchall()
    updated = 0

    for row in rows:
        try:
            guild_id = row["id"]
        except Exception:
            guild_id = row[0]
        old = get_guild_by_id(guild_id)["level"]
        new = recalculate_guild_level(guild_id)
        if new != old:
            updated += 1

    return updated


# ==============================
# ✅ GUILD JOURNAL CORE V1
# ==============================

# 7.0.8
# Журнал гільдії: перегляд останніх подій.


def get_guild_logs(guild_id, limit=20, offset=0):
    init_guild_system()
    ensure_guild_monthly_season(guild_id)

    try:
        limit = int(limit)
    except Exception:
        limit = 20

    try:
        offset = int(offset)
    except Exception:
        offset = 0

    limit = max(1, min(100, limit))
    offset = max(0, offset)

    cursor.execute("""
    SELECT *
    FROM guild_logs
    WHERE guild_id=?
    ORDER BY id DESC
    LIMIT ? OFFSET ?
    """, (
        guild_id,
        limit,
        offset,
    ))

    return cursor.fetchall()


def get_guild_logs_count(guild_id):
    init_guild_system()
    cursor.execute("SELECT COUNT(*) AS cnt FROM guild_logs WHERE guild_id=?", (guild_id,))
    row = cursor.fetchone()

    try:
        return int(row["cnt"] or 0)
    except Exception:
        return int(row[0] or 0) if row else 0


# ==============================
# ✅ GUILD JOURNAL CHARACTER NAMES CORE V1
# ==============================

# 7.0.8a
# Future logs: заявка до гільдії пише імʼя персонажа, а не user_id.

try:
    _base_create_guild_application_before_journal_names_v1 = create_guild_application
except Exception:
    _base_create_guild_application_before_journal_names_v1 = None


def create_guild_application(user_id, guild_id):
    """
    FINAL OVERRIDE:
    Подача заявки з журналом через character_name замість user_id.
    """

    init_guild_system()
    level_gate = get_guild_access_level_state(user_id)
    if not level_gate.get("success"):
        return {
            "success": False,
            "message": (
                f"❌ Вступ до гільдії доступний з {MIN_GUILD_ACCESS_LEVEL} рівня.\n"
                f"Твій поточний рівень: {level_gate.get('level', 0)}."
            ),
        }

    gate = can_user_join_or_create_guild(user_id)
    if not gate.get("success"):
        return gate

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

    applicant_name = get_character_name_by_user_id(user_id)

    add_guild_log(
        guild_id=guild_id,
        event_type="application_created",
        text=f"Нова заявка до гільдії від {applicant_name}."
    )

    return {
        "success": True,
        "message": "✅ Заявку до гільдії подано."
    }


# ==============================
# ✅ GUILD ACTIVITY REWARDS CORE V1
# ==============================

# 7.0.9
# Guild EXP / Resource integration points:
# - elite mob victory reward
# - contract completion reward helper

GUILD_ELITE_KILL_EXP_REWARD = 25
GUILD_ELITE_KILL_RESOURCE_REWARD = 1
GUILD_ELITE_KILL_SCORE_REASON = "Перемога над елітним мобом"

GUILD_CONTRACT_EXP_REWARD = 50
GUILD_CONTRACT_RESOURCE_REWARD = 3
GUILD_CONTRACT_SCORE_REASON = "Виконання контракту"


def _guild_activity_result_text(result):
    if not result or not result.get("success"):
        return None

    exp = int(result.get("exp", 0) or 0)
    resource = int(result.get("resource", 0) or 0)
    kills = int(result.get("kills", 0) or 0)
    contracts = int(result.get("contracts", 0) or 0)

    parts = []
    if exp:
        parts.append(f"+{exp} EXP")
    if resource:
        parts.append(f"+{resource} ресурс")
    if kills:
        parts.append(f"+{kills} вбивство")
    if contracts:
        parts.append(f"+{contracts} контракт")

    if not parts:
        return None

    return "🏰 Гільдія: " + ", ".join(parts)


def _get_guild_event_actor_name(user_id):
    """Resolve a character name for Guild log enrichment.

    A lazy Character System import avoids introducing a module-import cycle.
    Empty, invalid, or unavailable names intentionally produce an empty string,
    so Guild events keep their previous text without exposing a technical ID.
    """
    try:
        from systems.character_system import get_character_name

        actor_name = get_character_name(user_id)
        if actor_name is None:
            return ""

        actor_name = str(actor_name).strip()
        return actor_name
    except Exception:
        return ""

def award_guild_elite_kill(user_id, mob=None):
    """
    Нарахування прогресу гільдії за перемогу над елітним мобом.

    Повертає dict add_user_guild_progress або success=False, якщо гравець без гільдії.
    """

    member = get_user_guild_member(user_id)

    if not member:
        return {
            "success": False,
            "message": "Гравець не перебуває у гільдії."
        }

    mob_name = "елітним мобом"
    try:
        if mob:
            mob_name = mob.get("name") or mob.get("title") or mob_name
    except Exception:
        pass

    actor_name = str(_get_guild_event_actor_name(user_id) or "").strip()
    reason = f"{GUILD_ELITE_KILL_SCORE_REASON}: {mob_name}."
    if actor_name:
        reason += f" (переміг: {actor_name})"

    return add_user_guild_progress(
        user_id=user_id,
        exp=GUILD_ELITE_KILL_EXP_REWARD,
        resource=GUILD_ELITE_KILL_RESOURCE_REWARD,
        kills=1,
        contracts=0,
        reason=reason
    )



def award_guild_contract_completion(user_id, contract=None):
    """
    Нарахування прогресу гільдії за виконання контракту.

    Цю функцію можна викликати з системи контрактів після успішного завершення контракту.
    """

    member = get_user_guild_member(user_id)

    if not member:
        return {
            "success": False,
            "message": "Гравець не перебуває у гільдії."
        }

    contract_name = "контракт"
    try:
        if isinstance(contract, dict):
            contract_name = (
                contract.get("target_mob_name")
                or contract.get("name")
                or contract.get("title")
                or contract.get("contract_name")
                or contract_name
            )
        elif contract:
            contract_name = str(contract)
    except Exception:
        pass

    actor_name = str(_get_guild_event_actor_name(user_id) or "").strip()
    reason = f"{GUILD_CONTRACT_SCORE_REASON}: {contract_name}."
    if actor_name:
        reason += f" (виконав: {actor_name})"

    return add_user_guild_progress(
        user_id=user_id,
        exp=GUILD_CONTRACT_EXP_REWARD,
        resource=GUILD_CONTRACT_RESOURCE_REWARD,
        kills=0,
        contracts=1,
        reason=reason
    )



def get_guild_activity_reward_text(result):
    return _guild_activity_result_text(result)


# ==============================
# ✅ GUILD DIAGNOSTICS CORE V1
# ==============================

# 7.0.10
# Stabilization / cleanup / diagnostics helpers.


def get_guild_pending_applications_count(guild_id):
    init_guild_system()
    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM guild_applications WHERE guild_id=? AND status=?",
        (guild_id, GUILD_APPLICATION_PENDING)
    )
    row = cursor.fetchone()
    try:
        return int(row["cnt"] or 0)
    except Exception:
        return int(row[0] or 0) if row else 0


def get_user_pending_applications_count(user_id):
    init_guild_system()
    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM guild_applications WHERE user_id=? AND status=?",
        (user_id, GUILD_APPLICATION_PENDING)
    )
    row = cursor.fetchone()
    try:
        return int(row["cnt"] or 0)
    except Exception:
        return int(row[0] or 0) if row else 0


def get_guild_diagnostics(user_id):
    """
    Technical diagnostics for /guild_debug.
    Safe read-only helper.
    """

    init_guild_system()

    diagnostics = {
        "user_id": user_id,
        "season_key": get_current_guild_season_key(),
        "has_guild": False,
        "guild": None,
        "member": None,
        "member_count": 0,
        "pending_applications": 0,
        "user_pending_applications": 0,
        "officer_count": 0,
        "next_level_info": None,
    }

    try:
        member = get_user_guild_member(user_id)
        diagnostics["member"] = member
        diagnostics["user_pending_applications"] = get_user_pending_applications_count(user_id)

        if not member:
            return diagnostics

        guild = get_guild_by_id(member["guild_id"])
        diagnostics["guild"] = guild
        diagnostics["has_guild"] = bool(guild)

        if guild:
            ensure_guild_monthly_season(guild["id"])
            diagnostics["member_count"] = get_guild_member_count(guild["id"])
            diagnostics["pending_applications"] = get_guild_pending_applications_count(guild["id"])

            try:
                diagnostics["officer_count"] = get_guild_officer_count(guild["id"])
            except Exception:
                diagnostics["officer_count"] = 0

            try:
                diagnostics["next_level_info"] = get_guild_next_level_info(guild["id"])
            except Exception:
                diagnostics["next_level_info"] = None

    except Exception as error:
        diagnostics["error"] = str(error)

    return diagnostics


def run_guild_sanity_cleanup():
    """
    Conservative cleanup used by /guild_fix_states and startup-compatible calls:
    - stale pending applications for players already in guilds;
    - guild levels recalculation;
    - duplicate icon/index checks if available.
    """

    result = {
        "stale_applications": None,
        "levels_recalculated": None,
        "icons_checked": False,
        "ok": True,
        "errors": [],
    }

    try:
        try:
            result["stale_applications"] = cleanup_stale_guild_applications()
        except Exception as error:
            result["errors"].append(f"cleanup_stale_guild_applications: {error}")

        try:
            result["levels_recalculated"] = cleanup_recalculate_all_guild_levels()
        except Exception as error:
            result["errors"].append(f"cleanup_recalculate_all_guild_levels: {error}")

        try:
            ensure_unique_guild_icon_index()
            result["icons_checked"] = True
        except Exception as error:
            result["errors"].append(f"ensure_unique_guild_icon_index: {error}")

    except Exception as error:
        result["ok"] = False
        result["errors"].append(str(error))

    if result["errors"]:
        result["ok"] = False

    return result

