# -*- coding: utf-8 -*-
"""Presence and persistent activity session foundation for Stage 12.1.0."""
from __future__ import annotations

import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

LOGGER = logging.getLogger(__name__)
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "game.db"
PLAYER_ONLINE_TIMEOUT_SECONDS = 300
PLAYER_PRESENCE_WRITE_THROTTLE_SECONDS = 30
PLAYER_ACTIVITY_TYPES = frozenset(("trade_request", "trade", "duel_request", "pvp_battle"))

_PRESENCE_LOCK = threading.RLock()
_LAST_WRITE: dict[int, float] = {}
_INSTALL_LOCK = threading.RLock()


def _connect(db_path=None):
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def _now():
    return datetime.now(timezone.utc)


def _text(value=None):
    value = value or _now()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


def _parse(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def init_player_interaction_foundation(db_path=None):

    # Stage 14.1.0 PvP persistent foundation
    from systems.pvp_system import init_pvp_foundation, recover_pvp_after_restart
    init_pvp_foundation()
    recover_pvp_after_restart()
    conn = _connect(db_path)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        if not columns:
            raise RuntimeError("users table is missing; init_db() must run first")
        added = False
        if "last_activity_at" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN last_activity_at TEXT NULL")
            added = True
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS player_activity_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                activity_type TEXT NOT NULL CHECK (
                    activity_type IN ('trade_request','trade','duel_request','pvp_battle')
                ),
                reference_id INTEGER NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT NULL,
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_users_last_activity_at
                ON users(last_activity_at);
            CREATE INDEX IF NOT EXISTS idx_player_activity_sessions_expires_at
                ON player_activity_sessions(expires_at);
            CREATE INDEX IF NOT EXISTS idx_player_activity_sessions_type_status
                ON player_activity_sessions(activity_type, status);
        """)
        conn.commit()
    finally:
        conn.close()
    removed = expire_stale_player_activity_sessions(db_path=db_path)
    return {
        "success": True,
        "presence_column_added": added,
        "expired_sessions_removed": removed,
        "online_timeout_seconds": PLAYER_ONLINE_TIMEOUT_SECONDS,
        "write_throttle_seconds": PLAYER_PRESENCE_WRITE_THROTTLE_SECONDS,
    }


def touch_player_activity(user_id, *, force=False, now=None, db_path=None):
    uid = int(user_id)
    mono = time.monotonic()
    if not force:
        with _PRESENCE_LOCK:
            previous = _LAST_WRITE.get(uid)
            if previous is not None and mono - previous < PLAYER_PRESENCE_WRITE_THROTTLE_SECONDS:
                return {"success": True, "updated": False, "reason": "throttled"}
    conn = _connect(db_path)
    try:
        stamp = _text(now)
        cur = conn.execute("UPDATE users SET last_activity_at=? WHERE user_id=?", (stamp, uid))
        conn.commit()
        if cur.rowcount != 1:
            return {"success": False, "updated": False, "reason": "user_not_found"}
    finally:
        conn.close()
    with _PRESENCE_LOCK:
        _LAST_WRITE[uid] = mono
    return {"success": True, "updated": True, "last_activity_at": stamp}


def get_player_last_activity(user_id, db_path=None):
    conn = _connect(db_path)
    try:
        row = conn.execute("SELECT last_activity_at FROM users WHERE user_id=?", (int(user_id),)).fetchone()
        return _parse(row[0]) if row else None
    finally:
        conn.close()


def is_player_online(user_id, *, now=None, timeout_seconds=PLAYER_ONLINE_TIMEOUT_SECONDS, db_path=None):
    last = get_player_last_activity(user_id, db_path=db_path)
    if last is None:
        return False
    current = now or _now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    age = (current.astimezone(timezone.utc) - last).total_seconds()
    return 0 <= age <= max(0, int(timeout_seconds))


def expire_stale_player_activity_sessions(*, now=None, db_path=None):
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "DELETE FROM player_activity_sessions WHERE expires_at IS NOT NULL AND expires_at <= ?",
            (_text(now),),
        )
        conn.commit()
        return max(0, int(cur.rowcount))
    finally:
        conn.close()


def get_player_activity_session(user_id, *, include_expired=False, now=None, db_path=None):
    if not include_expired:
        expire_stale_player_activity_sessions(now=now, db_path=db_path)
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT id,user_id,activity_type,reference_id,status,created_at,updated_at,expires_at "
            "FROM player_activity_sessions WHERE user_id=?",
            (int(user_id),),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def acquire_player_activity_session(user_id, activity_type, *, reference_id=None,
                                    status="active", ttl_seconds=None, now=None, db_path=None):
    uid = int(user_id)
    kind = str(activity_type)
    if kind not in PLAYER_ACTIVITY_TYPES:
        return {"success": False, "reason": "invalid_activity_type"}
    current = now or _now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    stamp = _text(current)
    expires = _text(current + timedelta(seconds=int(ttl_seconds))) if ttl_seconds is not None else None
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "DELETE FROM player_activity_sessions "
            "WHERE user_id=? AND expires_at IS NOT NULL AND expires_at <= ?",
            (uid, stamp),
        )
        row = conn.execute(
            "SELECT id,activity_type,reference_id,status,expires_at "
            "FROM player_activity_sessions WHERE user_id=?", (uid,)
        ).fetchone()
        if row:
            conn.rollback()
            return {"success": False, "reason": "player_busy", "session": dict(row)}
        cur = conn.execute(
            "INSERT INTO player_activity_sessions "
            "(user_id,activity_type,reference_id,status,created_at,updated_at,expires_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (uid, kind, reference_id, str(status), stamp, stamp, expires),
        )
        conn.commit()
        return {"success": True, "session_id": int(cur.lastrowid), "expires_at": expires}
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        return {"success": False, "reason": "integrity_error", "error": str(exc)}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def refresh_player_activity_session(user_id, *, expected_activity_type=None,
                                    status=None, ttl_seconds=None, now=None, db_path=None):
    current = now or _now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    clauses = ["updated_at=?"]
    params: list[Any] = [_text(current)]
    expires = None
    if status is not None:
        clauses.append("status=?")
        params.append(str(status))
    if ttl_seconds is not None:
        expires = _text(current + timedelta(seconds=int(ttl_seconds)))
        clauses.append("expires_at=?")
        params.append(expires)
    query = "UPDATE player_activity_sessions SET " + ",".join(clauses) + " WHERE user_id=?"
    params.append(int(user_id))
    if expected_activity_type is not None:
        query += " AND activity_type=?"
        params.append(str(expected_activity_type))
    conn = _connect(db_path)
    try:
        cur = conn.execute(query, tuple(params))
        conn.commit()
        return {"success": cur.rowcount == 1, "updated": cur.rowcount == 1, "expires_at": expires}
    finally:
        conn.close()


def release_player_activity_session(user_id, *, activity_type=None, reference_id=None, db_path=None):
    query = "DELETE FROM player_activity_sessions WHERE user_id=?"
    params: list[Any] = [int(user_id)]
    if activity_type is not None:
        query += " AND activity_type=?"
        params.append(str(activity_type))
    if reference_id is not None:
        query += " AND reference_id=?"
        params.append(int(reference_id))
    conn = _connect(db_path)
    try:
        cur = conn.execute(query, tuple(params))
        conn.commit()
        return {"success": True, "released": max(0, int(cur.rowcount))}
    finally:
        conn.close()


def is_player_interaction_busy(user_id, db_path=None):
    return get_player_activity_session(user_id, db_path=db_path) is not None


def _extract_update_user_ids(updates: Iterable[Any]):
    result = set()
    for update in updates or ():
        for name in ("message", "edited_message", "channel_post", "edited_channel_post",
                     "callback_query", "inline_query", "chosen_inline_result",
                     "shipping_query", "pre_checkout_query"):
            obj = getattr(update, name, None)
            if obj is None:
                continue
            actor = getattr(obj, "from_user", None)
            uid = getattr(actor, "id", None) if actor is not None else None
            if uid is not None:
                try:
                    result.add(int(uid))
                except (TypeError, ValueError):
                    pass
    return result


def install_player_presence_tracking(bot, db_path=None):
    """Touch presence before TeleBot dispatch; never block polling on DB errors."""
    with _INSTALL_LOCK:
        if getattr(bot, "_rom_presence_tracker_12_1_0", False):
            return {"success": True, "installed": False, "reason": "already_installed"}
        original = getattr(bot, "process_new_updates", None)
        if not callable(original):
            raise RuntimeError("bot.process_new_updates is unavailable")

        def wrapped(updates):
            for uid in _extract_update_user_ids(updates):
                try:
                    touch_player_activity(uid, db_path=db_path)
                except Exception as exc:
                    LOGGER.warning("Presence update failed for user %s: %s", uid, exc)
            return original(updates)

        bot.process_new_updates = wrapped
        bot._rom_presence_tracker_12_1_0 = True
        bot._rom_presence_original_process_new_updates = original
        return {"success": True, "installed": True}

# ROM 12.2.0 MAP LOCATION PLAYER DISCOVERY
PLAYER_DISCOVERY_PAGE_SIZE = 8


def _users_column_names(conn):
    return {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}


def _pick_user_column(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def get_online_players_in_same_location(user_id, *, page=0,
                                        page_size=PLAYER_DISCOVERY_PAGE_SIZE,
                                        now=None, db_path=None):
    """Return online registered characters from the viewer's current location.

    The viewer is never included. Results are deterministically sorted and paged.
    """
    uid = int(user_id)
    page = max(0, int(page))
    page_size = max(1, min(20, int(page_size)))
    current = now or _now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    cutoff = _text(current - timedelta(seconds=PLAYER_ONLINE_TIMEOUT_SECONDS))
    conn = _connect(db_path)
    try:
        columns = _users_column_names(conn)
        location_col = _pick_user_column(columns, ("current_location", "location"))
        name_col = _pick_user_column(columns, ("character_name", "name", "username"))
        level_col = _pick_user_column(columns, ("level", "player_level"))
        class_col = _pick_user_column(columns, ("character_class", "class_name", "class"))
        if location_col is None or name_col is None:
            raise RuntimeError("users location/name columns are unavailable")
        viewer = conn.execute(
            f'SELECT "{location_col}" AS location FROM users WHERE user_id=?',
            (uid,),
        ).fetchone()
        if not viewer or not viewer["location"]:
            return {"success": False, "reason": "viewer_location_missing", "players": []}
        select_level = f'"{level_col}"' if level_col else "NULL"
        select_class = f'"{class_col}"' if class_col else "NULL"
        rows = conn.execute(
            f'SELECT user_id, "{name_col}" AS character_name, '
            f'{select_level} AS level, {select_class} AS character_class, '
            f'"{location_col}" AS current_location, last_activity_at '
            f'FROM users WHERE user_id<>? AND "{location_col}"=? '
            f'AND last_activity_at IS NOT NULL AND last_activity_at>=? '
            f'AND TRIM(COALESCE("{name_col}", ""))<>"" '
            f'ORDER BY LOWER("{name_col}"), user_id',
            (uid, viewer["location"], cutoff),
        ).fetchall()
        players = [dict(row) for row in rows]
        total = len(players)
        start = page * page_size
        selected = players[start:start + page_size]
        return {
            "success": True,
            "location": viewer["location"],
            "players": selected,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": max(1, (total + page_size - 1) // page_size),
            "has_previous": page > 0,
            "has_next": start + page_size < total,
        }
    finally:
        conn.close()


def get_public_player_interaction_profile(viewer_id, target_id, *, now=None, db_path=None):
    viewer_id = int(viewer_id)
    target_id = int(target_id)
    if viewer_id == target_id:
        return {"success": False, "reason": "self_target"}
    current = now or _now()
    conn = _connect(db_path)
    try:
        columns = _users_column_names(conn)
        location_col = _pick_user_column(columns, ("current_location", "location"))
        name_col = _pick_user_column(columns, ("character_name", "name", "username"))
        level_col = _pick_user_column(columns, ("level", "player_level"))
        class_col = _pick_user_column(columns, ("character_class", "class_name", "class"))
        if location_col is None or name_col is None:
            raise RuntimeError("users location/name columns are unavailable")
        level_expr = f'"{level_col}"' if level_col else "NULL"
        class_expr = f'"{class_col}"' if class_col else "NULL"
        viewer = conn.execute(
            f'SELECT "{location_col}" AS location FROM users WHERE user_id=?',
            (viewer_id,),
        ).fetchone()
        target = conn.execute(
            f'SELECT user_id, "{name_col}" AS character_name, {level_expr} AS level, '
            f'{class_expr} AS character_class, "{location_col}" AS current_location, '
            f'last_activity_at FROM users WHERE user_id=?',
            (target_id,),
        ).fetchone()
        if not viewer or not target:
            return {"success": False, "reason": "player_not_found"}
        if viewer["location"] != target["current_location"]:
            return {"success": False, "reason": "different_location"}
        last = _parse(target["last_activity_at"])
        if last is None:
            return {"success": False, "reason": "player_offline"}
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        age = (current.astimezone(timezone.utc) - last).total_seconds()
        if age < 0 or age > PLAYER_ONLINE_TIMEOUT_SECONDS:
            return {"success": False, "reason": "player_offline"}
        result = dict(target)
        result.update({"success": True, "online": True})
        return result
    finally:
        conn.close()

# ROM 12.3.0 PLAYER INTERACTION REQUESTS
PLAYER_INTERACTION_REQUEST_TYPES = frozenset(("trade", "duel"))
PLAYER_INTERACTION_REQUEST_STATUSES = frozenset(("pending", "accepted", "declined", "cancelled", "expired"))
PLAYER_INTERACTION_REQUEST_TTL_SECONDS = 120


def _init_player_interaction_request_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS player_interaction_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_type TEXT NOT NULL CHECK(request_type IN ('trade','duel')),
            initiator_user_id INTEGER NOT NULL,
            recipient_user_id INTEGER NOT NULL,
            location_snapshot TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(
                status IN ('pending','accepted','declined','cancelled','expired')
            ),
            revision INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            responded_at TEXT NULL,
            FOREIGN KEY(initiator_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY(recipient_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            CHECK(initiator_user_id <> recipient_user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_player_interaction_requests_recipient_status_expiry
            ON player_interaction_requests(recipient_user_id, status, expires_at);
        CREATE INDEX IF NOT EXISTS idx_player_interaction_requests_initiator_status
            ON player_interaction_requests(initiator_user_id, status);
    """)


def init_player_interaction_requests(db_path=None):
    conn = _connect(db_path)
    try:
        _init_player_interaction_request_schema(conn)
        conn.commit()
    finally:
        conn.close()
    expired = expire_stale_interaction_requests(db_path=db_path)
    return {"success": True, "table": "player_interaction_requests", "expired_requests": expired}


def _request_user_row(conn, user_id):
    columns = _users_column_names(conn)
    location_col = _pick_user_column(columns, ("current_location", "location"))
    name_col = _pick_user_column(columns, ("character_name", "name", "username"))
    if location_col is None or name_col is None:
        raise RuntimeError("users location/name columns are unavailable")
    return conn.execute(
        f'SELECT user_id, "{name_col}" AS character_name, '
        f'"{location_col}" AS current_location, last_activity_at '
        f'FROM users WHERE user_id=?',
        (int(user_id),),
    ).fetchone()


def _row_online(row, current):
    last = _parse(row["last_activity_at"]) if row else None
    if last is None:
        return False
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    age = (current.astimezone(timezone.utc) - last).total_seconds()
    return 0 <= age <= PLAYER_ONLINE_TIMEOUT_SECONDS


def get_interaction_request(request_id, *, db_path=None):
    conn = _connect(db_path)
    try:
        _init_player_interaction_request_schema(conn)
        row = conn.execute(
            "SELECT id,request_type,initiator_user_id,recipient_user_id,location_snapshot,"
            "status,revision,created_at,updated_at,expires_at,responded_at "
            "FROM player_interaction_requests WHERE id=?",
            (int(request_id),),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_player_interaction_request(initiator_user_id, recipient_user_id, request_type,
                                      *, ttl_seconds=PLAYER_INTERACTION_REQUEST_TTL_SECONDS,
                                      now=None, db_path=None, pve_busy_checker=None):
    """Atomically create a request and reserve both players' activity slots."""
    initiator = int(initiator_user_id)
    recipient = int(recipient_user_id)
    kind = str(request_type)
    if kind not in PLAYER_INTERACTION_REQUEST_TYPES:
        return {"success": False, "reason": "invalid_request_type"}
    if initiator == recipient:
        return {"success": False, "reason": "self_target"}
    current = now or _now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    stamp = _text(current)
    expires = _text(current + timedelta(seconds=max(1, int(ttl_seconds))))
    if callable(pve_busy_checker):
        if pve_busy_checker(initiator) or pve_busy_checker(recipient):
            return {"success": False, "reason": "player_in_battle"}

    # ROM 12.3.2: stale sessions must never produce a false player_busy.
    cleanup_player_interaction_state(now=current, db_path=db_path)

    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        _init_player_interaction_request_schema(conn)
        conn.execute(
            "DELETE FROM player_activity_sessions WHERE expires_at IS NOT NULL AND expires_at<=?",
            (stamp,),
        )
        a = _request_user_row(conn, initiator)
        b = _request_user_row(conn, recipient)
        if not a or not b:
            conn.rollback(); return {"success": False, "reason": "player_not_found"}
        if not _row_online(a, current) or not _row_online(b, current):
            conn.rollback(); return {"success": False, "reason": "player_offline"}
        if not a["current_location"] or a["current_location"] != b["current_location"]:
            conn.rollback(); return {"success": False, "reason": "different_location"}
        busy = conn.execute(
            "SELECT user_id,activity_type,status FROM player_activity_sessions "
            "WHERE user_id IN (?,?) ORDER BY user_id", (initiator, recipient)
        ).fetchall()
        if busy:
            conn.rollback()
            return {"success": False, "reason": "player_busy", "busy": [dict(x) for x in busy]}
        cur = conn.execute(
            "INSERT INTO player_interaction_requests "
            "(request_type,initiator_user_id,recipient_user_id,location_snapshot,status,revision,"
            "created_at,updated_at,expires_at) VALUES (?,?,?,?, 'pending',1,?,?,?)",
            (kind, initiator, recipient, a["current_location"], stamp, stamp, expires),
        )
        request_id = int(cur.lastrowid)
        activity_type = f"{kind}_request"
        conn.executemany(
            "INSERT INTO player_activity_sessions "
            "(user_id,activity_type,reference_id,status,created_at,updated_at,expires_at) "
            "VALUES (?,?,?,'pending',?,?,?)",
            ((initiator, activity_type, request_id, stamp, stamp, expires),
             (recipient, activity_type, request_id, stamp, stamp, expires)),
        )
        conn.commit()
        return {
            "success": True, "request_id": request_id, "request_type": kind,
            "initiator_user_id": initiator, "recipient_user_id": recipient,
            "initiator_name": a["character_name"], "recipient_name": b["character_name"],
            "location": a["current_location"], "revision": 1, "expires_at": expires,
        }
    except sqlite3.IntegrityError as exc:
        conn.rollback(); return {"success": False, "reason": "integrity_error", "error": str(exc)}
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def respond_to_player_interaction_request(request_id, actor_user_id, action,
                                          *, expected_revision=1, now=None,
                                          db_path=None, pve_busy_checker=None):
    """Accept or decline a pending request with actor, expiry and revision guards."""
    request_id = int(request_id); actor = int(actor_user_id); action = str(action)
    if action not in ("accept", "decline"):
        return {"success": False, "reason": "invalid_action"}
    current = now or _now()
    if current.tzinfo is None: current = current.replace(tzinfo=timezone.utc)
    stamp = _text(current)
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        _init_player_interaction_request_schema(conn)
        row = conn.execute("SELECT * FROM player_interaction_requests WHERE id=?", (request_id,)).fetchone()
        if not row:
            conn.rollback(); return {"success": False, "reason": "request_not_found"}
        row = dict(row)
        if actor != int(row["recipient_user_id"]):
            conn.rollback(); return {"success": False, "reason": "wrong_actor"}
        if row["status"] != "pending":
            conn.rollback(); return {"success": False, "reason": "request_not_pending", "status": row["status"]}
        if int(row["revision"]) != int(expected_revision):
            conn.rollback(); return {"success": False, "reason": "stale_revision"}
        expiry = _parse(row["expires_at"])
        if expiry is None or expiry <= current:
            conn.execute("UPDATE player_interaction_requests SET status='expired',updated_at=?,responded_at=? WHERE id=?", (stamp, stamp, request_id))
            conn.execute("DELETE FROM player_activity_sessions WHERE reference_id=? AND activity_type=?", (request_id, f"{row['request_type']}_request"))
            conn.commit(); return {"success": False, "reason": "request_expired"}
        if action == "decline":
            conn.execute("UPDATE player_interaction_requests SET status='declined',updated_at=?,responded_at=? WHERE id=?", (stamp, stamp, request_id))
            conn.execute("DELETE FROM player_activity_sessions WHERE reference_id=? AND activity_type=?", (request_id, f"{row['request_type']}_request"))
            conn.commit(); return {**row, "success": True, "status": "declined"}
        if callable(pve_busy_checker):
            if pve_busy_checker(int(row["initiator_user_id"])) or pve_busy_checker(int(row["recipient_user_id"])):
                conn.rollback(); return {"success": False, "reason": "player_in_battle"}
        a = _request_user_row(conn, row["initiator_user_id"]); b = _request_user_row(conn, row["recipient_user_id"])
        if not a or not b:
            conn.rollback(); return {"success": False, "reason": "player_not_found"}
        if not _row_online(a,current) or not _row_online(b,current):
            conn.rollback(); return {"success": False, "reason": "player_offline"}
        if a["current_location"] != row["location_snapshot"] or b["current_location"] != row["location_snapshot"]:
            conn.rollback(); return {"success": False, "reason": "different_location"}
        conn.execute("UPDATE player_interaction_requests SET status='accepted',updated_at=?,responded_at=? WHERE id=?", (stamp, stamp, request_id))
        # Request transition commits first; trade creation is idempotent and owns
        # the next transaction, activity lock and ten-minute editing timeout.
        conn.execute(
            "DELETE FROM player_activity_sessions WHERE reference_id=? AND activity_type=?",
            (request_id, f"{row['request_type']}_request"),
        )
        conn.commit()
        if row["request_type"] == "trade":
            trade_result = create_player_trade_from_accepted_request(request_id, now=current, db_path=db_path)
            if not trade_result.get("success"):
                return {**row, "success": False, "reason": "trade_creation_failed", "trade_error": trade_result}
            return {**row, "success": True, "status": "accepted", "trade": trade_result}
        return {**row, "success": True, "status": "accepted"}
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def cancel_player_interaction_request(request_id, actor_user_id, *, now=None, db_path=None):
    request_id=int(request_id); actor=int(actor_user_id); stamp=_text(now)
    conn=_connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        row=conn.execute("SELECT * FROM player_interaction_requests WHERE id=?",(request_id,)).fetchone()
        if not row:
            conn.rollback(); return {"success":False,"reason":"request_not_found"}
        row=dict(row)
        if actor not in (int(row["initiator_user_id"]),int(row["recipient_user_id"])):
            conn.rollback(); return {"success":False,"reason":"wrong_actor"}
        if row["status"] != "pending":
            conn.rollback(); return {"success":False,"reason":"request_not_pending","status":row["status"]}
        conn.execute("UPDATE player_interaction_requests SET status='cancelled',updated_at=?,responded_at=? WHERE id=?",(stamp,stamp,request_id))
        conn.execute("DELETE FROM player_activity_sessions WHERE reference_id=? AND activity_type=?",(request_id,f"{row['request_type']}_request"))
        conn.commit(); return {**row,"success":True,"status":"cancelled"}
    except Exception:
        conn.rollback(); raise
    finally: conn.close()


def expire_stale_interaction_requests(*, now=None, db_path=None):
    stamp=_text(now); conn=_connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE"); _init_player_interaction_request_schema(conn)
        rows=conn.execute("SELECT id,request_type FROM player_interaction_requests WHERE status='pending' AND expires_at<=?",(stamp,)).fetchall()
        for row in rows:
            conn.execute("UPDATE player_interaction_requests SET status='expired',updated_at=?,responded_at=? WHERE id=?",(stamp,stamp,row["id"]))
            conn.execute("DELETE FROM player_activity_sessions WHERE reference_id=? AND activity_type=?",(row["id"],f"{row['request_type']}_request"))
        conn.commit(); return len(rows)
    except Exception:
        conn.rollback(); raise
    finally: conn.close()

# ROM 12.3.2 INTERACTION SESSION TIMEOUT AND RECOVERY
PLACEHOLDER_ACCEPTED_TRADE_SESSION_TTL_SECONDS = 0
FUTURE_TRADE_EDITING_TTL_SECONDS = 600
FUTURE_TRADE_CONFIRMATION_TTL_SECONDS = 120


def _table_exists(conn, table_name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (str(table_name),),
    ).fetchone() is not None


def recover_orphan_player_activity_sessions(*, now=None, db_path=None):
    """Release stale request sessions and pre-editor accepted trade placeholders.

    Stage 12.3 has no player_trades table or offer editor yet. Therefore an
    accepted request must not retain permanent activity_type='trade' rows.
    Future real trades are preserved as soon as player_trades exists and owns
    the referenced trade session.
    """
    stamp = _text(now)
    conn = _connect(db_path)
    counters = {
        "expired_sessions": 0,
        "orphan_request_sessions": 0,
        "terminal_request_sessions": 0,
        "accepted_placeholder_trade_sessions": 0,
        "missing_user_sessions": 0,
    }
    try:
        conn.execute("BEGIN IMMEDIATE")
        request_table = _table_exists(conn, "player_interaction_requests")
        trade_table = _table_exists(conn, "player_trades")

        cur = conn.execute(
            "DELETE FROM player_activity_sessions "
            "WHERE expires_at IS NOT NULL AND expires_at<=?",
            (stamp,),
        )
        counters["expired_sessions"] = max(0, int(cur.rowcount))

        cur = conn.execute(
            "DELETE FROM player_activity_sessions "
            "WHERE user_id NOT IN (SELECT user_id FROM users)"
        )
        counters["missing_user_sessions"] = max(0, int(cur.rowcount))

        if request_table:
            cur = conn.execute(
                "DELETE FROM player_activity_sessions "
                "WHERE activity_type IN ('trade_request','duel_request') "
                "AND NOT EXISTS ("
                "  SELECT 1 FROM player_interaction_requests r "
                "  WHERE r.id=player_activity_sessions.reference_id"
                ")"
            )
            counters["orphan_request_sessions"] = max(0, int(cur.rowcount))

            cur = conn.execute(
                "DELETE FROM player_activity_sessions "
                "WHERE activity_type IN ('trade_request','duel_request') "
                "AND EXISTS ("
                "  SELECT 1 FROM player_interaction_requests r "
                "  WHERE r.id=player_activity_sessions.reference_id "
                "  AND r.status IN ('accepted','declined','cancelled','expired')"
                ")"
            )
            counters["terminal_request_sessions"] = max(0, int(cur.rowcount))

            if not trade_table:
                cur = conn.execute(
                    "DELETE FROM player_activity_sessions "
                    "WHERE activity_type='trade' "
                    "AND EXISTS ("
                    "  SELECT 1 FROM player_interaction_requests r "
                    "  WHERE r.id=player_activity_sessions.reference_id "
                    "  AND r.request_type='trade' AND r.status='accepted'"
                    ")"
                )
                counters["accepted_placeholder_trade_sessions"] = max(0, int(cur.rowcount))
            else:
                # Preserve only sessions backed by a real active player_trades row.
                cur = conn.execute(
                    "DELETE FROM player_activity_sessions "
                    "WHERE activity_type='trade' "
                    "AND NOT EXISTS ("
                    "  SELECT 1 FROM player_trades t "
                    "  WHERE t.id=player_activity_sessions.reference_id "
                    "  AND t.status IN ('editing','confirming','committing')"
                    ")"
                )
                counters["accepted_placeholder_trade_sessions"] = max(0, int(cur.rowcount))

        conn.commit()
        counters["total_removed"] = sum(counters.values())
        return {"success": True, **counters}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def cleanup_player_interaction_state(*, now=None, db_path=None):
    """Canonical lightweight cleanup before availability/busy checks."""
    expired_requests = 0
    if _database_has_table("player_interaction_requests", db_path=db_path):
        expired_requests = expire_stale_interaction_requests(now=now, db_path=db_path)
    recovered = recover_orphan_player_activity_sessions(now=now, db_path=db_path)
    return {
        "success": True,
        "expired_requests": expired_requests,
        "recovery": recovered,
    }


def _database_has_table(table_name, *, db_path=None):
    conn = _connect(db_path)
    try:
        return _table_exists(conn, table_name)
    finally:
        conn.close()

# ROM 12.4.0 PLAYER TRADE DATABASE AND HISTORY FOUNDATION
PLAYER_TRADE_EDITING_TTL_SECONDS = 600
PLAYER_TRADE_CONFIRMATION_TTL_SECONDS = 120
PLAYER_TRADE_ACTIVE_STATUSES = frozenset(("editing", "confirming", "committing"))
PLAYER_TRADE_TERMINAL_STATUSES = frozenset(("completed", "cancelled", "expired", "failed"))


def _init_player_trade_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS player_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NULL UNIQUE,
            initiator_user_id INTEGER NOT NULL,
            recipient_user_id INTEGER NOT NULL,
            location_snapshot TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'editing' CHECK(
                status IN ('editing','confirming','committing','completed','cancelled','expired','failed')
            ),
            revision INTEGER NOT NULL DEFAULT 1,
            initiator_ready INTEGER NOT NULL DEFAULT 0 CHECK(initiator_ready IN (0,1)),
            recipient_ready INTEGER NOT NULL DEFAULT 0 CHECK(recipient_ready IN (0,1)),
            initiator_confirmed INTEGER NOT NULL DEFAULT 0 CHECK(initiator_confirmed IN (0,1)),
            recipient_confirmed INTEGER NOT NULL DEFAULT 0 CHECK(recipient_confirmed IN (0,1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            completed_at TEXT NULL,
            cancelled_at TEXT NULL,
            cancel_reason TEXT NULL,
            FOREIGN KEY(request_id) REFERENCES player_interaction_requests(id) ON DELETE SET NULL,
            FOREIGN KEY(initiator_user_id) REFERENCES users(user_id) ON DELETE RESTRICT,
            FOREIGN KEY(recipient_user_id) REFERENCES users(user_id) ON DELETE RESTRICT,
            CHECK(initiator_user_id <> recipient_user_id)
        );
        CREATE TABLE IF NOT EXISTS player_trade_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER NOT NULL,
            owner_user_id INTEGER NOT NULL,
            asset_type TEXT NOT NULL CHECK(asset_type IN ('stack','equipment','gold')),
            inventory_id INTEGER NULL,
            item_id INTEGER NULL,
            quantity INTEGER NULL,
            gold_amount REAL NULL,
            snapshot_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(trade_id) REFERENCES player_trades(id) ON DELETE CASCADE,
            FOREIGN KEY(owner_user_id) REFERENCES users(user_id) ON DELETE RESTRICT,
            CHECK(quantity IS NULL OR quantity > 0),
            CHECK(gold_amount IS NULL OR gold_amount >= 0)
        );
        CREATE TABLE IF NOT EXISTS player_trade_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER NOT NULL,
            actor_user_id INTEGER NULL,
            event_type TEXT NOT NULL,
            revision INTEGER NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(trade_id) REFERENCES player_trades(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS player_trade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER NOT NULL UNIQUE,
            initiator_user_id INTEGER NOT NULL,
            recipient_user_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('completed','cancelled','expired','failed')),
            initiator_offer_snapshot TEXT NOT NULL DEFAULT '[]',
            recipient_offer_snapshot TEXT NOT NULL DEFAULT '[]',
            summary_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            completed_at TEXT NULL,
            cancelled_at TEXT NULL,
            cancel_reason TEXT NULL,
            FOREIGN KEY(trade_id) REFERENCES player_trades(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_player_trades_initiator_status
            ON player_trades(initiator_user_id, status);
        CREATE INDEX IF NOT EXISTS idx_player_trades_recipient_status
            ON player_trades(recipient_user_id, status);
        CREATE INDEX IF NOT EXISTS idx_player_trades_status_expiry
            ON player_trades(status, expires_at);
        CREATE INDEX IF NOT EXISTS idx_player_trade_offers_trade_owner
            ON player_trade_offers(trade_id, owner_user_id);
        CREATE INDEX IF NOT EXISTS idx_player_trade_events_trade_id
            ON player_trade_events(trade_id, id);
        CREATE INDEX IF NOT EXISTS idx_player_trade_history_initiator
            ON player_trade_history(initiator_user_id, id DESC);
        CREATE INDEX IF NOT EXISTS idx_player_trade_history_recipient
            ON player_trade_history(recipient_user_id, id DESC);
    """)


def init_player_trade_foundation(db_path=None):
    conn = _connect(db_path)
    try:
        _init_player_interaction_request_schema(conn)
        _init_player_trade_schema(conn)
        conn.commit()
    finally:
        conn.close()
    expired = expire_stale_player_trades(db_path=db_path)
    return {"success": True, "tables": ["player_trades", "player_trade_offers", "player_trade_events", "player_trade_history"], "expired_trades": expired}


def _trade_event(conn, trade_id, actor_user_id, event_type, revision, stamp, payload_json="{}"):
    conn.execute(
        "INSERT INTO player_trade_events(trade_id,actor_user_id,event_type,revision,payload_json,created_at) VALUES(?,?,?,?,?,?)",
        (int(trade_id), actor_user_id, str(event_type), int(revision), str(payload_json), stamp),
    )


def _write_trade_history(conn, trade, status, stamp, reason=None):
    completed_at = stamp if status == "completed" else None
    cancelled_at = stamp if status in ("cancelled", "expired", "failed") else None
    conn.execute(
        "INSERT OR IGNORE INTO player_trade_history "
        "(trade_id,initiator_user_id,recipient_user_id,status,initiator_offer_snapshot,recipient_offer_snapshot,summary_json,created_at,completed_at,cancelled_at,cancel_reason) "
        "VALUES(?,?,?,?,'[]','[]','{}',?,?,?,?)",
        (trade["id"], trade["initiator_user_id"], trade["recipient_user_id"], status,
         trade["created_at"], completed_at, cancelled_at, reason),
    )


def create_player_trade_from_accepted_request(request_id, *, now=None, db_path=None):
    """Create exactly one editing trade and move both activity locks to trade_id."""
    request_id = int(request_id)
    current = now or _now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    stamp = _text(current)
    expires = _text(current + timedelta(seconds=PLAYER_TRADE_EDITING_TTL_SECONDS))
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        _init_player_trade_schema(conn)
        request = conn.execute("SELECT * FROM player_interaction_requests WHERE id=?", (request_id,)).fetchone()
        if not request:
            conn.rollback(); return {"success": False, "reason": "request_not_found"}
        request = dict(request)
        if request["request_type"] != "trade" or request["status"] != "accepted":
            conn.rollback(); return {"success": False, "reason": "request_not_accepted"}
        existing = conn.execute("SELECT * FROM player_trades WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            conn.rollback(); return {"success": True, "created": False, "trade": dict(existing)}
        cur = conn.execute(
            "INSERT INTO player_trades(request_id,initiator_user_id,recipient_user_id,location_snapshot,status,revision,created_at,updated_at,expires_at) "
            "VALUES(?,?,?,?,'editing',1,?,?,?)",
            (request_id, request["initiator_user_id"], request["recipient_user_id"], request["location_snapshot"], stamp, stamp, expires),
        )
        trade_id = int(cur.lastrowid)
        conn.execute("DELETE FROM player_activity_sessions WHERE user_id IN (?,?)", (request["initiator_user_id"], request["recipient_user_id"]))
        conn.executemany(
            "INSERT INTO player_activity_sessions(user_id,activity_type,reference_id,status,created_at,updated_at,expires_at) VALUES(?,'trade',?,'editing',?,?,?)",
            ((request["initiator_user_id"], trade_id, stamp, stamp, expires),
             (request["recipient_user_id"], trade_id, stamp, stamp, expires)),
        )
        _trade_event(conn, trade_id, None, "created", 1, stamp, '{"source":"accepted_request"}')
        conn.commit()
        return {"success": True, "created": True, "trade_id": trade_id, "status": "editing", "revision": 1, "expires_at": expires,
                "initiator_user_id": request["initiator_user_id"], "recipient_user_id": request["recipient_user_id"]}
    except sqlite3.IntegrityError as exc:
        conn.rollback(); return {"success": False, "reason": "integrity_error", "error": str(exc)}
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


# ROM 12.6.5 PLAYER TRADE LOCK CONSOLIDATION AND STARTUP RECOVERY

def recover_active_player_trades_after_restart(*, now=None, db_path=None):
    """Cancel every unfinished direct trade during process startup.

    In-memory Telegram UI/input state cannot safely survive a process restart.
    This transaction cancels active trades, releases activity sessions and item
    reservations, and records normal trade event/history entries.
    """
    stamp = _text(now)
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        _init_player_trade_schema(conn)
        rows = conn.execute(
            "SELECT * FROM player_trades "
            "WHERE status IN ('editing','confirming','committing') "
            "ORDER BY id"
        ).fetchall()
        participants = set()
        trade_ids = []
        for row in rows:
            trade = dict(row)
            trade_id = int(trade["id"])
            participants.add(int(trade["initiator_user_id"]))
            participants.add(int(trade["recipient_user_id"]))
            trade_ids.append(trade_id)
            conn.execute(
                "UPDATE player_trades SET status='cancelled',updated_at=?,"
                "cancelled_at=?,cancel_reason='server_restart' "
                "WHERE id=? AND status IN ('editing','confirming','committing')",
                (stamp, stamp, trade_id),
            )
            conn.execute(
                "DELETE FROM player_activity_sessions "
                "WHERE activity_type='trade' AND reference_id=?",
                (trade_id,),
            )
            if _table_exists(conn, "inventory_reservations"):
                conn.execute(
                    "DELETE FROM inventory_reservations "
                    "WHERE reservation_type='player_trade' AND reference_id=?",
                    (trade_id,),
                )
            _trade_event(
                conn, trade_id, None, "cancelled",
                int(trade.get("revision") or 1), stamp,
                '{"reason":"server_restart"}',
            )
            _write_trade_history(
                conn, trade, "cancelled", stamp, "server_restart"
            )
        conn.commit()
        return {
            "success": True,
            "cancelled_trades": len(trade_ids),
            "trade_ids": trade_ids,
            "participant_user_ids": sorted(participants),
            "reason": "server_restart",
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_player_trade(trade_id, *, db_path=None):
    conn = _connect(db_path)
    try:
        _init_player_trade_schema(conn)
        row = conn.execute("SELECT * FROM player_trades WHERE id=?", (int(trade_id),)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_active_player_trade(user_id, *, now=None, db_path=None):
    expire_stale_player_trades(now=now, db_path=db_path)
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM player_trades WHERE (initiator_user_id=? OR recipient_user_id=?) "
            "AND status IN ('editing','confirming','committing') ORDER BY id DESC LIMIT 1",
            (int(user_id), int(user_id)),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_player_trade_events(trade_id, *, db_path=None):
    conn = _connect(db_path)
    try:
        return [dict(row) for row in conn.execute("SELECT * FROM player_trade_events WHERE trade_id=? ORDER BY id", (int(trade_id),)).fetchall()]
    finally:
        conn.close()


def get_player_trade_history(user_id, *, page=0, page_size=10, db_path=None):
    page=max(0,int(page)); page_size=max(1,min(50,int(page_size))); offset=page*page_size
    conn=_connect(db_path)
    try:
        rows=conn.execute(
            "SELECT * FROM player_trade_history WHERE initiator_user_id=? OR recipient_user_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
            (int(user_id),int(user_id),page_size,offset),
        ).fetchall()
        return [dict(row) for row in rows]
    finally: conn.close()


def cancel_player_trade(trade_id, actor_user_id, *, reason="user_cancelled", now=None, db_path=None):
    trade_id=int(trade_id); actor=int(actor_user_id); stamp=_text(now)
    conn=_connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE"); _init_player_trade_schema(conn)
        row=conn.execute("SELECT * FROM player_trades WHERE id=?",(trade_id,)).fetchone()
        if not row:
            conn.rollback(); return {"success":False,"reason":"trade_not_found"}
        trade=dict(row)
        if actor not in (int(trade["initiator_user_id"]),int(trade["recipient_user_id"])):
            conn.rollback(); return {"success":False,"reason":"wrong_actor"}
        if trade["status"] not in PLAYER_TRADE_ACTIVE_STATUSES:
            conn.rollback(); return {"success":False,"reason":"trade_not_active","status":trade["status"]}
        conn.execute("UPDATE player_trades SET status='cancelled',updated_at=?,cancelled_at=?,cancel_reason=? WHERE id=?",(stamp,stamp,str(reason),trade_id))
        conn.execute("DELETE FROM player_activity_sessions WHERE activity_type='trade' AND reference_id=?",(trade_id,))
        # Compatibility: older isolated tests and partially migrated databases
        # may not have the Stage 12.5 reservation table yet.
        if _table_exists(conn, "inventory_reservations"):
            conn.execute("DELETE FROM inventory_reservations WHERE reservation_type='player_trade' AND reference_id=?",(trade_id,))
        _trade_event(conn,trade_id,actor,"cancelled",trade["revision"],stamp,'{}')
        _write_trade_history(conn,trade,"cancelled",stamp,str(reason))
        conn.commit(); return {**trade,"success":True,"status":"cancelled","cancel_reason":str(reason)}
    except Exception:
        conn.rollback(); raise
    finally: conn.close()


def expire_stale_player_trades(*, now=None, db_path=None):
    stamp=_text(now); conn=_connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE"); _init_player_trade_schema(conn)
        rows=conn.execute("SELECT * FROM player_trades WHERE status IN ('editing','confirming') AND expires_at<=?",(stamp,)).fetchall()
        for row in rows:
            trade=dict(row)
            conn.execute("UPDATE player_trades SET status='expired',updated_at=?,cancelled_at=?,cancel_reason='timeout' WHERE id=?",(stamp,stamp,trade["id"]))
            conn.execute("DELETE FROM player_activity_sessions WHERE activity_type='trade' AND reference_id=?",(trade["id"],))
            # Compatibility: expiration must work before/without the optional
            # reservation schema in isolated legacy tests.
            if _table_exists(conn, "inventory_reservations"):
                conn.execute("DELETE FROM inventory_reservations WHERE reservation_type='player_trade' AND reference_id=?",(trade["id"],))
            _trade_event(conn,trade["id"],None,"expired",trade["revision"],stamp,'{}')
            _write_trade_history(conn,trade,"expired",stamp,"timeout")
        conn.commit(); return len(rows)
    except Exception:
        conn.rollback(); raise
    finally: conn.close()

# ROM 12.5.0 PLAYER TRADE ITEM POLICY AND RESERVATIONS
TRADE_BLOCKED_ITEM_IDS = frozenset((501, 602, 726, 728))
TRADE_ALLOWED_SPECIAL_ITEM_IDS = frozenset((601, 727))
TRADE_BLOCKED_CATEGORIES = frozenset(("trash", "gray_loot", "grey_loot", "quest", "dev", "premium_bound"))
TRADE_RESERVATION_TYPE = "player_trade"


def _init_inventory_reservation_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS inventory_reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            reservation_type TEXT NOT NULL,
            reference_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY(inventory_id) REFERENCES inventory(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            UNIQUE(inventory_id, reservation_type, reference_id)
        );
        CREATE INDEX IF NOT EXISTS idx_inventory_reservations_inventory
            ON inventory_reservations(inventory_id);
        CREATE INDEX IF NOT EXISTS idx_inventory_reservations_user
            ON inventory_reservations(user_id);
        CREATE INDEX IF NOT EXISTS idx_inventory_reservations_reference
            ON inventory_reservations(reference_id, reservation_type);
        CREATE INDEX IF NOT EXISTS idx_inventory_reservations_expiry
            ON inventory_reservations(expires_at);
    """)


def init_player_trade_item_policy_and_reservations(db_path=None):
    conn = _connect(db_path)
    try:
        _init_inventory_reservation_schema(conn)
        conn.commit()
    finally:
        conn.close()
    recovery = recover_orphan_inventory_reservations(db_path=db_path)
    return {
        "success": True,
        "table": "inventory_reservations",
        "blocked_item_ids": sorted(TRADE_BLOCKED_ITEM_IDS),
        "allowed_special_item_ids": sorted(TRADE_ALLOWED_SPECIAL_ITEM_IDS),
        "recovery": recovery,
    }


def _inventory_columns(conn):
    return {row[1] for row in conn.execute("PRAGMA table_info(inventory)").fetchall()}


def _items_columns(conn):
    return {row[1] for row in conn.execute("PRAGMA table_info(items)").fetchall()}


def _first_existing(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _active_auction_reserved_quantity(conn, inventory_id):
    if not _table_exists(conn, "auction_lots"):
        return 0
    columns = {row[1] for row in conn.execute("PRAGMA table_info(auction_lots)").fetchall()}
    if "item_ref_id" not in columns or "status" not in columns:
        return 0
    quantity_expr = "quantity" if "quantity" in columns else "1"
    source_clause = ""
    params = [int(inventory_id)]
    if "item_source" in columns:
        source_clause = " AND item_source IN ('inventory','generated_equipment','equipment')"
    row = conn.execute(
        f"SELECT COALESCE(SUM({quantity_expr}),0) FROM auction_lots "
        f"WHERE item_ref_id=? AND status='active'{source_clause}",
        tuple(params),
    ).fetchone()
    return int(row[0] or 0)


def _inventory_is_equipped(conn, user_id, inventory_id):
    if not _table_exists(conn, "equipment_slots"):
        return False
    row = conn.execute(
        "SELECT 1 FROM equipment_slots WHERE user_id=? AND inventory_id=? LIMIT 1",
        (int(user_id), int(inventory_id)),
    ).fetchone()
    return row is not None


def _trade_policy_result(tradeable, reason, message, **extra):
    return {"tradeable": bool(tradeable), "reason": str(reason), "message": str(message), **extra}


def get_inventory_reserved_quantity(inventory_id, *, exclude_reference_id=None, db_path=None):
    conn = _connect(db_path)
    try:
        _init_inventory_reservation_schema(conn)
        query = "SELECT COALESCE(SUM(quantity),0) FROM inventory_reservations WHERE inventory_id=?"
        params = [int(inventory_id)]
        if exclude_reference_id is not None:
            query += " AND NOT (reservation_type=? AND reference_id=?)"
            params.extend((TRADE_RESERVATION_TYPE, int(exclude_reference_id)))
        return int(conn.execute(query, tuple(params)).fetchone()[0] or 0)
    finally:
        conn.close()


def get_inventory_available_quantity(user_id, inventory_id, *, exclude_reference_id=None, db_path=None):
    conn = _connect(db_path)
    try:
        inv_columns = _inventory_columns(conn)
        quantity_col = _first_existing(inv_columns, ("quantity", "qty", "count"))
        if quantity_col is None:
            return 0
        row = conn.execute(
            f'SELECT "{quantity_col}" FROM inventory WHERE id=? AND user_id=?',
            (int(inventory_id), int(user_id)),
        ).fetchone()
        if not row:
            return 0
        reserved = conn.execute(
            "SELECT COALESCE(SUM(quantity),0) FROM inventory_reservations "
            "WHERE inventory_id=?" +
            (" AND NOT (reservation_type=? AND reference_id=?)" if exclude_reference_id is not None else ""),
            ((int(inventory_id), TRADE_RESERVATION_TYPE, int(exclude_reference_id))
             if exclude_reference_id is not None else (int(inventory_id),)),
        ).fetchone()[0]
        auction = _active_auction_reserved_quantity(conn, inventory_id)
        return max(0, int(row[0] or 0) - int(reserved or 0) - int(auction or 0))
    finally:
        conn.close()


def _trade_base_build_item_snapshot_12_6_3(user_id, inventory_id, *, db_path=None):
    """Build an immutable JSON-ready snapshot, including socketed runes when available."""
    conn = _connect(db_path)
    try:
        inv_columns = _inventory_columns(conn)
        item_columns = _items_columns(conn)
        inventory_select = ["inv.id AS inventory_id", "inv.user_id", "inv.item_id"]
        for column in ("quantity", "durability", "max_durability", "refine_level"):
            inventory_select.append(f'inv."{column}" AS "{column}"' if column in inv_columns else f'NULL AS "{column}"')
        item_select = []
        for output, candidates in (
            ("item_name", ("name", "item_name")),
            ("category", ("category", "item_type", "type")),
            ("rarity", ("rarity",)),
            ("level", ("level", "required_level")),
            ("tradeable", ("tradeable",)),
            # ROM 17.4.3 TRADE SNAPSHOT EQUIPMENT TYPE FIELDS
            ("slot_key", ("slot_key", "equipment_slot", "slot")),
            ("armor_type", ("armor_type",)),
            ("item_subtype", ("item_subtype", "subtype")),
            ("type", ("type",)),
        ):
            column = _first_existing(item_columns, candidates)
            item_select.append(f'i."{column}" AS "{output}"' if column else f'NULL AS "{output}"')
        row = conn.execute(
            "SELECT " + ",".join(inventory_select + item_select) +
            " FROM inventory inv JOIN items i ON i.id=inv.item_id WHERE inv.id=? AND inv.user_id=?",
            (int(inventory_id), int(user_id)),
        ).fetchone()
        if not row:
            return None
        snapshot = dict(row)
        snapshot["runes"] = []
        if _table_exists(conn, "inventory_runes"):
            rune_columns = {x[1] for x in conn.execute("PRAGMA table_info(inventory_runes)").fetchall()}
            inventory_fk = _first_existing(rune_columns, ("inventory_id", "equipment_inventory_id"))
            rune_id_col = _first_existing(rune_columns, ("rune_item_id", "item_id", "rune_id"))
            slot_col = _first_existing(rune_columns, ("slot_index", "socket_index", "slot"))
            if inventory_fk and rune_id_col:
                slot_expr = f'ir."{slot_col}"' if slot_col else "NULL"
                rows = conn.execute(
                    f'SELECT ir."{rune_id_col}" AS rune_item_id,{slot_expr} AS slot_index,'
                    f'COALESCE(i.name, "") AS rune_name FROM inventory_runes ir '
                    f'LEFT JOIN items i ON i.id=ir."{rune_id_col}" WHERE ir."{inventory_fk}"=? '
                    f'ORDER BY slot_index, rune_item_id',
                    (int(inventory_id),),
                ).fetchall()
                snapshot["runes"] = [dict(x) for x in rows]
        return snapshot
    finally:
        conn.close()


def get_item_trade_policy(user_id, inventory_id, requested_quantity=1, *, trade_id=None, db_path=None):
    """Canonical tradeability resolver for stacks and generated equipment."""
    uid = int(user_id)
    inv_id = int(inventory_id)
    try:
        requested = int(requested_quantity)
    except (TypeError, ValueError):
        return _trade_policy_result(False, "invalid_quantity", "Кількість предмета вказана некоректно.")
    if requested <= 0:
        return _trade_policy_result(False, "invalid_quantity", "Кількість предмета повинна бути більшою за нуль.")

    conn = _connect(db_path)
    try:
        _init_inventory_reservation_schema(conn)
        inv_columns = _inventory_columns(conn)
        item_columns = _items_columns(conn)
        quantity_col = _first_existing(inv_columns, ("quantity", "qty", "count"))
        durability_col = _first_existing(inv_columns, ("durability", "durability_current"))
        select = ["inv.id AS inventory_id", "inv.user_id", "inv.item_id"]
        select.append(f'inv."{quantity_col}" AS quantity' if quantity_col else "1 AS quantity")
        select.append(f'inv."{durability_col}" AS durability' if durability_col else "NULL AS durability")
        for output, candidates in (
            ("category", ("category", "item_type", "type")),
            ("tradeable", ("tradeable",)),
            ("bound_type", ("bound_type", "binding", "bind_type")),
            ("dev_only", ("dev_only", "is_dev")),
            ("premium_bound", ("premium_bound", "is_premium_bound")),
        ):
            column = _first_existing(item_columns, candidates)
            select.append(f'i."{column}" AS "{output}"' if column else f'NULL AS "{output}"')
        row = conn.execute(
            "SELECT " + ",".join(select) + " FROM inventory inv JOIN items i ON i.id=inv.item_id "
            "WHERE inv.id=? AND inv.user_id=?",
            (inv_id, uid),
        ).fetchone()
        if not row:
            return _trade_policy_result(False, "not_owned", "Предмет не знайдено у вашому інвентарі.")
        item = dict(row)
        item_id = int(item["item_id"])
        category = str(item.get("category") or "").strip().lower()
        bound_type = str(item.get("bound_type") or "").strip().lower()

        if item_id in TRADE_BLOCKED_ITEM_IDS:
            messages = {
                501: "Сферу нового шляху не можна передавати.",
                602: "Руну Успіху не можна передавати.",
                726: "Жетони Фіріуса не можна передавати.",
                728: "Досконалий Екстрактор не можна передавати.",
            }
            return _trade_policy_result(False, "protected_item", messages[item_id], item_id=item_id)
        if category in TRADE_BLOCKED_CATEGORIES or "trash" in category:
            return _trade_policy_result(False, "gray_loot", "Сірий лут не можна передавати.", item_id=item_id)
        # Specific binding policies must win over the generic tradeable=False
        # fallback so callers receive the correct machine reason and message.
        if bound_type in ("quest", "class", "dev", "premium", "premium_bound", "soulbound", "bound"):
            return _trade_policy_result(False, "bound_item", "Прив’язаний предмет не можна передавати.", item_id=item_id)
        if item.get("dev_only") not in (None, 0, "0", False):
            return _trade_policy_result(False, "dev_only", "Службовий DEV-предмет не можна передавати.", item_id=item_id)
        if item.get("premium_bound") not in (None, 0, "0", False):
            return _trade_policy_result(False, "premium_bound", "Premium-bound предмет не можна передавати.", item_id=item_id)
        if item.get("tradeable") is not None and int(item["tradeable"] or 0) == 0 and item_id not in TRADE_ALLOWED_SPECIAL_ITEM_IDS:
            return _trade_policy_result(False, "tradeable_false", "Цей предмет не можна передавати.", item_id=item_id)
        if _inventory_is_equipped(conn, uid, inv_id):
            return _trade_policy_result(False, "equipped", "Екіпірований предмет не можна передавати.", item_id=item_id)
        if item.get("durability") is not None and int(item["durability"]) <= 0:
            return _trade_policy_result(False, "broken", "Зламане спорядження не можна передавати.", item_id=item_id)
        auction_reserved = _active_auction_reserved_quantity(conn, inv_id)
        if auction_reserved > 0:
            return _trade_policy_result(False, "auction_reserved", "Предмет уже використовується в Торговому Домі.", item_id=item_id)

        query = "SELECT COALESCE(SUM(quantity),0) FROM inventory_reservations WHERE inventory_id=?"
        params = [inv_id]
        if trade_id is not None:
            query += " AND NOT (reservation_type=? AND reference_id=?)"
            params.extend((TRADE_RESERVATION_TYPE, int(trade_id)))
        reserved = int(conn.execute(query, tuple(params)).fetchone()[0] or 0)
        actual = int(item.get("quantity") or 1)
        available = max(0, actual - reserved - auction_reserved)
        if requested > available:
            reason = "already_reserved" if reserved else "insufficient_quantity"
            message = "Предмет уже зарезервований для іншої операції." if reserved else "Недостатньо доступної кількості предмета."
            return _trade_policy_result(False, reason, message, item_id=item_id, available_quantity=available)
        snapshot = build_trade_item_snapshot(uid, inv_id, db_path=db_path)
        return _trade_policy_result(True, "allowed", "Предмет можна додати до обміну.", item_id=item_id,
                                    available_quantity=available, requested_quantity=requested, snapshot=snapshot)
    finally:
        conn.close()


def reserve_inventory_for_trade(trade_id, user_id, inventory_id, quantity=1, *, now=None, db_path=None):
    trade_id=int(trade_id); uid=int(user_id); inv_id=int(inventory_id); quantity=int(quantity)
    conn=_connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        _init_inventory_reservation_schema(conn)
        trade=conn.execute("SELECT * FROM player_trades WHERE id=?",(trade_id,)).fetchone()
        if not trade:
            conn.rollback(); return {"success":False,"reason":"trade_not_found"}
        trade=dict(trade)
        if trade["status"] != "editing":
            conn.rollback(); return {"success":False,"reason":"trade_not_editing"}
        if uid not in (int(trade["initiator_user_id"]),int(trade["recipient_user_id"])):
            conn.rollback(); return {"success":False,"reason":"wrong_actor"}
        policy=get_item_trade_policy(uid,inv_id,quantity,trade_id=trade_id,db_path=db_path)
        if not policy.get("tradeable"):
            conn.rollback(); return {"success":False,**policy}
        stamp=_text(now)
        conn.execute(
            "INSERT INTO inventory_reservations(inventory_id,user_id,quantity,reservation_type,reference_id,created_at,expires_at) "
            "VALUES(?,?,?,?,?,?,?) ON CONFLICT(inventory_id,reservation_type,reference_id) DO UPDATE SET "
            "quantity=excluded.quantity,expires_at=excluded.expires_at",
            (inv_id,uid,quantity,TRADE_RESERVATION_TYPE,trade_id,stamp,trade["expires_at"]),
        )
        conn.commit(); return {"success":True,"trade_id":trade_id,"inventory_id":inv_id,"quantity":quantity,"policy":policy}
    except sqlite3.IntegrityError as exc:
        conn.rollback(); return {"success":False,"reason":"integrity_error","error":str(exc)}
    except Exception:
        conn.rollback(); raise
    finally: conn.close()


def release_trade_inventory_reservations(trade_id, *, db_path=None):
    conn=_connect(db_path)
    try:
        cur=conn.execute("DELETE FROM inventory_reservations WHERE reservation_type=? AND reference_id=?",(TRADE_RESERVATION_TYPE,int(trade_id)))
        conn.commit(); return max(0,int(cur.rowcount))
    finally: conn.close()


def assert_inventory_not_reserved(inventory_id, *, requested_quantity=1, exclude_trade_id=None, db_path=None):
    reserved=get_inventory_reserved_quantity(inventory_id,exclude_reference_id=exclude_trade_id,db_path=db_path)
    if reserved >= int(requested_quantity):
        return {"success":False,"reason":"inventory_reserved","reserved_quantity":reserved,
                "message":"Предмет уже зарезервований для обміну."}
    return {"success":True,"reserved_quantity":reserved}


def recover_orphan_inventory_reservations(*, now=None, db_path=None):
    stamp=_text(now); conn=_connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE"); _init_inventory_reservation_schema(conn)
        expired=conn.execute("DELETE FROM inventory_reservations WHERE expires_at<=?",(stamp,)).rowcount
        orphan=0
        if _table_exists(conn,"player_trades"):
            cur=conn.execute(
                "DELETE FROM inventory_reservations WHERE reservation_type=? AND ("
                "NOT EXISTS(SELECT 1 FROM player_trades t WHERE t.id=inventory_reservations.reference_id) OR "
                "EXISTS(SELECT 1 FROM player_trades t WHERE t.id=inventory_reservations.reference_id "
                "AND t.status IN ('completed','cancelled','expired','failed')))"
                ,(TRADE_RESERVATION_TYPE,))
            orphan=max(0,int(cur.rowcount))
        owner_mismatch=conn.execute(
            "DELETE FROM inventory_reservations WHERE NOT EXISTS("
            "SELECT 1 FROM inventory inv WHERE inv.id=inventory_reservations.inventory_id "
            "AND inv.user_id=inventory_reservations.user_id)"
        ).rowcount
        conn.commit()
        return {"success":True,"expired":max(0,int(expired)),"orphan_or_terminal":orphan,
                "owner_mismatch":max(0,int(owner_mismatch)),
                "total_removed":max(0,int(expired))+orphan+max(0,int(owner_mismatch))}
    except Exception:
        conn.rollback(); raise
    finally: conn.close()

# ROM 12.6.0 PLAYER TRADE OFFER EDITOR
import json

PLAYER_TRADE_OFFER_PAGE_SIZE = 8


def _trade_offer_actor(trade, user_id):
    uid = int(user_id)
    if uid == int(trade["initiator_user_id"]):
        return "initiator"
    if uid == int(trade["recipient_user_id"]):
        return "recipient"
    return None



def _trade_actor_offer_locked_12_7_0(trade, user_id):
    side, ready_col, _ = _trade_side_columns_12_7_0(trade, user_id)
    return bool(side and int(trade.get(ready_col) or 0))

def _trade_offer_mutation(conn, trade, actor_user_id, event_type, stamp, payload):
    """Invalidate only the actor's offer-ready state and both final confirms."""
    side, ready_col, _ = _trade_side_columns_12_7_0(trade, actor_user_id)
    if not side:
        raise ValueError("trade mutation actor is not a participant")
    new_revision = int(trade["revision"] or 0) + 1
    expires_at = _text(
        _parse(stamp) + timedelta(seconds=PLAYER_TRADE_EDITING_TTL_SECONDS)
    )
    conn.execute(
        f"UPDATE player_trades SET status='editing',revision=?,{ready_col}=0,"
        "initiator_confirmed=0,recipient_confirmed=0,updated_at=?,expires_at=? "
        "WHERE id=?",
        (new_revision, stamp, expires_at, int(trade["id"])),
    )
    _trade_event(
        conn,
        int(trade["id"]),
        int(actor_user_id),
        event_type,
        new_revision,
        stamp,
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
    )
    return new_revision, expires_at


def get_player_trade_offers(trade_id, *, db_path=None):
    conn = _connect(db_path)
    try:
        _init_player_trade_schema(conn)
        rows = conn.execute(
            "SELECT * FROM player_trade_offers WHERE trade_id=? "
            "ORDER BY owner_user_id, CASE asset_type WHEN 'gold' THEN 0 ELSE 1 END, id",
            (int(trade_id),),
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            try:
                item["snapshot"] = json.loads(item.get("snapshot_json") or "{}")
            except Exception:
                item["snapshot"] = {}
            result.append(item)
        return result
    finally:
        conn.close()


def get_player_trade_editor_state(trade_id, viewer_user_id, *, now=None, db_path=None):
    expire_stale_player_trades(now=now, db_path=db_path)
    trade = get_player_trade(trade_id, db_path=db_path)
    if not trade:
        return {"success": False, "reason": "trade_not_found"}
    side = _trade_offer_actor(trade, viewer_user_id)
    if not side:
        return {"success": False, "reason": "wrong_actor"}
    if trade["status"] not in PLAYER_TRADE_ACTIVE_STATUSES:
        return {"success": False, "reason": "trade_not_active", "trade": trade}
    offers = get_player_trade_offers(trade_id, db_path=db_path)
    own = [x for x in offers if int(x["owner_user_id"]) == int(viewer_user_id)]
    other = [x for x in offers if int(x["owner_user_id"]) != int(viewer_user_id)]
    other_user_id = (int(trade["recipient_user_id"]) if side == "initiator"
                     else int(trade["initiator_user_id"]))
    return {
        "success": True,
        "trade": trade,
        "side": side,
        "viewer_user_id": int(viewer_user_id),
        "other_user_id": other_user_id,
        "own_offers": own,
        "other_offers": other,
    }




def set_player_trade_item_offer(trade_id, owner_user_id, inventory_id, quantity=1, *, now=None, db_path=None):
    trade_id = int(trade_id); uid = int(owner_user_id); inv_id = int(inventory_id)
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return {"success": False, "reason": "invalid_quantity", "message": "Некоректна кількість."}
    if quantity <= 0:
        return remove_player_trade_item_offer(trade_id, uid, inv_id, now=now, db_path=db_path)
    policy = get_item_trade_policy(uid, inv_id, quantity, trade_id=trade_id, db_path=db_path)
    if not policy.get("tradeable"):
        return {"success": False, **policy}
    reserved = reserve_inventory_for_trade(trade_id, uid, inv_id, quantity, now=now, db_path=db_path)
    if not reserved.get("success"):
        return reserved
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE"); _init_player_trade_schema(conn)
        trade_row = conn.execute("SELECT * FROM player_trades WHERE id=?", (trade_id,)).fetchone()
        if not trade_row:
            conn.rollback(); return {"success": False, "reason": "trade_not_found"}
        trade = dict(trade_row)
        if trade["status"] != "editing" or not _trade_offer_actor(trade, uid):
            conn.rollback(); return {"success": False, "reason": "trade_not_editing"}
        if _trade_actor_offer_locked_12_7_0(trade, uid):
            conn.rollback(); return {"success": False, "reason": "own_offer_locked", "message": "Ваша пропозиція вже зафіксована. Натисніть «↩️ Змінити свою пропозицію»."}
        snapshot = policy.get("snapshot") or {}
        asset_type = "equipment" if int(snapshot.get("quantity") or 1) <= 1 else "stack"
        existing = conn.execute(
            "SELECT id FROM player_trade_offers WHERE trade_id=? AND owner_user_id=? AND inventory_id=?",
            (trade_id, uid, inv_id),
        ).fetchone()
        stamp = _text(now)
        payload = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
        if existing:
            conn.execute(
                "UPDATE player_trade_offers SET asset_type=?,item_id=?,quantity=?,snapshot_json=?,updated_at=? WHERE id=?",
                (asset_type, int(snapshot.get("item_id") or policy.get("item_id")), quantity, payload, stamp, int(existing[0])),
            )
        else:
            conn.execute(
                "INSERT INTO player_trade_offers(trade_id,owner_user_id,asset_type,inventory_id,item_id,quantity,gold_amount,snapshot_json,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?,NULL,?,?,?)",
                (trade_id, uid, asset_type, inv_id, int(snapshot.get("item_id") or policy.get("item_id")), quantity, payload, stamp, stamp),
            )
        revision, expires_at = _trade_offer_mutation(
            conn, trade, uid, "offer_item_set", stamp,
            {"inventory_id": inv_id, "item_id": int(snapshot.get("item_id") or policy.get("item_id")), "quantity": quantity},
        )
        conn.commit()
        return {"success": True, "trade_id": trade_id, "inventory_id": inv_id, "quantity": quantity,
                "revision": revision, "expires_at": expires_at}
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def remove_player_trade_item_offer(trade_id, owner_user_id, inventory_id, *, now=None, db_path=None):
    trade_id = int(trade_id); uid = int(owner_user_id); inv_id = int(inventory_id)
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE"); _init_player_trade_schema(conn); _init_inventory_reservation_schema(conn)
        trade_row = conn.execute("SELECT * FROM player_trades WHERE id=?", (trade_id,)).fetchone()
        if not trade_row:
            conn.rollback(); return {"success": False, "reason": "trade_not_found"}
        trade = dict(trade_row)
        if trade["status"] != "editing" or not _trade_offer_actor(trade, uid):
            conn.rollback(); return {"success": False, "reason": "trade_not_editing"}
        if _trade_actor_offer_locked_12_7_0(trade, uid):
            conn.rollback(); return {"success": False, "reason": "own_offer_locked", "message": "Ваша пропозиція вже зафіксована. Натисніть «↩️ Змінити свою пропозицію»."}
        deleted = conn.execute(
            "DELETE FROM player_trade_offers WHERE trade_id=? AND owner_user_id=? AND inventory_id=?",
            (trade_id, uid, inv_id),
        ).rowcount
        conn.execute(
            "DELETE FROM inventory_reservations WHERE inventory_id=? AND user_id=? AND reservation_type=? AND reference_id=?",
            (inv_id, uid, TRADE_RESERVATION_TYPE, trade_id),
        )
        if not deleted:
            conn.rollback(); return {"success": False, "reason": "offer_not_found"}
        stamp = _text(now)
        revision, expires_at = _trade_offer_mutation(
            conn, trade, uid, "offer_item_removed", stamp, {"inventory_id": inv_id})
        conn.commit()
        return {"success": True, "trade_id": trade_id, "inventory_id": inv_id,
                "revision": revision, "expires_at": expires_at}
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def set_player_trade_gold_offer(trade_id, owner_user_id, gold_amount, *, now=None, db_path=None):
    trade_id = int(trade_id); uid = int(owner_user_id)
    try:
        amount = round(float(gold_amount), 2)
    except (TypeError, ValueError):
        return {"success": False, "reason": "invalid_gold", "message": "Некоректна сума золота."}
    if amount < 0:
        return {"success": False, "reason": "invalid_gold", "message": "Сума золота не може бути від’ємною."}
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE"); _init_player_trade_schema(conn)
        trade_row = conn.execute("SELECT * FROM player_trades WHERE id=?", (trade_id,)).fetchone()
        if not trade_row:
            conn.rollback(); return {"success": False, "reason": "trade_not_found"}
        trade = dict(trade_row)
        if trade["status"] != "editing" or not _trade_offer_actor(trade, uid):
            conn.rollback(); return {"success": False, "reason": "trade_not_editing"}
        if _trade_actor_offer_locked_12_7_0(trade, uid):
            conn.rollback(); return {"success": False, "reason": "own_offer_locked", "message": "Ваша пропозиція вже зафіксована. Натисніть «↩️ Змінити свою пропозицію»."}
        wallet = conn.execute("SELECT gold FROM users WHERE user_id=?", (uid,)).fetchone()
        available = round(float((wallet[0] if wallet else 0) or 0), 2)
        if amount > available:
            conn.rollback(); return {"success": False, "reason": "insufficient_gold",
                                     "message": "Недостатньо золота.", "available_gold": available}
        stamp = _text(now)
        conn.execute("DELETE FROM player_trade_offers WHERE trade_id=? AND owner_user_id=? AND asset_type='gold'",
                     (trade_id, uid))
        if amount > 0:
            conn.execute(
                "INSERT INTO player_trade_offers(trade_id,owner_user_id,asset_type,inventory_id,item_id,quantity,gold_amount,snapshot_json,created_at,updated_at) "
                "VALUES(?,?,'gold',NULL,NULL,NULL,?,'{}',?,?)",
                (trade_id, uid, amount, stamp, stamp),
            )
        revision, expires_at = _trade_offer_mutation(
            conn, trade, uid, "offer_gold_set", stamp, {"gold_amount": amount})
        conn.commit()
        return {"success": True, "trade_id": trade_id, "gold_amount": amount,
                "available_gold": available, "revision": revision, "expires_at": expires_at}
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()

# ROM 12.6.1 PLAYER TRADE OFFER EDITOR UX

def _trade_offer_is_equipment_snapshot(snapshot):
    """Classify equipment without allowing stack-category durability defaults to win.

    Some inventory rows expose durability/max_durability defaults even for
    runes, materials, potions and consumables. Their canonical item category
    must take precedence over those compatibility fields.
    """
    snapshot = snapshot or {}
    category = str(snapshot.get("category") or "").strip().lower()
    stack_categories = {
        "rune", "runes", "stat_rune",
        "potion", "potions", "heal_potion", "mana_potion",
        "material", "materials", "special_material", "refine_material",
        "consumable", "consumables",
    }
    if category in stack_categories:
        return False
    if category in ("equipment", "weapon", "armor", "jewelry"):
        return True
    if str(snapshot.get("slot_key") or "").strip():
        return True
    return (
        snapshot.get("durability") is not None
        or snapshot.get("max_durability") is not None
    )


def get_trade_offer_entry(trade_id, owner_user_id, inventory_id, *, db_path=None):
    offers = get_player_trade_offers(trade_id, db_path=db_path)
    for offer in offers:
        if (int(offer.get("owner_user_id") or 0) == int(owner_user_id)
                and int(offer.get("inventory_id") or 0) == int(inventory_id)):
            return offer
    return None


def get_tradeable_inventory_for_trade(trade_id, user_id, *, page=0, page_size=8, db_path=None):
    """List only inventory quantities that can still be added to this offer.

    Equipment already offered disappears. A stack remains visible only while a
    positive quantity is not yet included in the current player's offer.
    """
    state = get_player_trade_editor_state(trade_id, user_id, db_path=db_path)
    if not state.get("success"):
        return state
    page = max(0, int(page or 0))
    page_size = max(1, min(20, int(page_size or 8)))
    offered_by_inventory = {
        int(x["inventory_id"]): int(x.get("quantity") or 1)
        for x in state.get("own_offers", []) if x.get("inventory_id") is not None
    }
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT inv.id FROM inventory inv WHERE inv.user_id=? ORDER BY inv.id DESC",
            (int(user_id),),
        ).fetchall()
    finally:
        conn.close()
    items = []
    for row in rows:
        inventory_id = int(row[0])
        policy = get_item_trade_policy(
            user_id, inventory_id, 1, trade_id=trade_id, db_path=db_path)
        if not policy.get("tradeable"):
            continue
        snapshot = policy.get("snapshot") or {}
        total_available = int(policy.get("available_quantity") or 0)
        offered_quantity = int(offered_by_inventory.get(inventory_id, 0))
        remaining_quantity = max(0, total_available - offered_quantity)
        if remaining_quantity <= 0:
            continue
        is_equipment = _trade_offer_is_equipment_snapshot(snapshot)
        items.append({
            "inventory_id": inventory_id,
            "available_quantity": remaining_quantity,
            "total_available_quantity": total_available,
            "offered_quantity": offered_quantity,
            "is_equipment": is_equipment,
            "is_stack": not is_equipment,
            "snapshot": snapshot,
        })
    total = len(items)
    start = page * page_size
    if start >= total and page > 0:
        page = max(0, (max(0, total - 1)) // page_size)
        start = page * page_size
    selected = items[start:start + page_size]
    return {
        "success": True, "trade_id": int(trade_id), "page": page,
        "page_size": page_size, "total": total,
        "has_previous": page > 0,
        "has_next": start + page_size < total,
        "items": selected,
    }


def add_all_available_to_trade_offer(trade_id, owner_user_id, inventory_id, *, now=None, db_path=None):
    policy = get_item_trade_policy(
        owner_user_id, inventory_id, 1, trade_id=trade_id, db_path=db_path)
    if not policy.get("tradeable"):
        return {"success": False, **policy}
    quantity = int(policy.get("available_quantity") or 0)
    if quantity <= 0:
        return {"success": False, "reason": "nothing_available",
                "message": "Увесь доступний стек уже додано до пропозиції."}
    return set_player_trade_item_offer(
        trade_id, owner_user_id, inventory_id, quantity, now=now, db_path=db_path)

# ROM 12.6.2 PLAYER TRADE ITEM PREVIEW AND WALLET UX

def get_player_trade_wallet_state(trade_id, user_id, *, db_path=None):
    state = get_player_trade_editor_state(trade_id, user_id, db_path=db_path)
    if not state.get("success"):
        return state
    conn = _connect(db_path)
    try:
        row = conn.execute("SELECT gold FROM users WHERE user_id=?", (int(user_id),)).fetchone()
    finally:
        conn.close()
    wallet_gold = round(float((row[0] if row else 0) or 0), 2)
    offered_gold = round(sum(
        float(x.get("gold_amount") or 0)
        for x in state.get("own_offers", []) if x.get("asset_type") == "gold"
    ), 2)
    return {
        "success": True,
        "wallet_gold": wallet_gold,
        "offered_gold": offered_gold,
        "remaining_gold": round(max(0.0, wallet_gold - offered_gold), 2),
    }


def get_trade_item_preview(trade_id, user_id, inventory_id, *, db_path=None):
    state = get_player_trade_editor_state(trade_id, user_id, db_path=db_path)
    if not state.get("success"):
        return state
    policy = get_item_trade_policy(
        user_id, inventory_id, 1, trade_id=trade_id, db_path=db_path)
    if not policy.get("tradeable"):
        return {"success": False, **policy}
    snapshot = dict(policy.get("snapshot") or {})
    existing = get_trade_offer_entry(trade_id, user_id, inventory_id, db_path=db_path)
    offered_quantity = int((existing or {}).get("quantity") or 0)
    maximum_quantity = int(policy.get("available_quantity") or 0)
    is_equipment = _trade_offer_is_equipment_snapshot(snapshot)
    return {
        "success": True,
        "trade_id": int(trade_id),
        "inventory_id": int(inventory_id),
        "snapshot": snapshot,
        "is_equipment": is_equipment,
        "is_stack": not is_equipment,
        "offered_quantity": offered_quantity,
        "maximum_quantity": maximum_quantity,
        "remaining_quantity": max(0, maximum_quantity - offered_quantity),
    }

# ROM 12.6.3 PLAYER TRADE PREVIEW DETAILS AND AMOUNT INPUT
_TRADE_PREVIEW_ITEM_FIELDS_12_6_3 = (
    "item_level","slot_key","item_subtype","armor_type","weapon_hands",
    "weapon_attack_type","weapon_min_damage","weapon_max_damage",
    "weapon_min_magic_damage","weapon_max_magic_damage","bonus_str",
    "bonus_dex","bonus_int","bonus_wis","bonus_sta","pdef","mdef",
)

def build_trade_item_snapshot(user_id, inventory_id, *, db_path=None):
    snapshot=_trade_base_build_item_snapshot_12_6_3(user_id,inventory_id,db_path=db_path)
    if not snapshot: return snapshot
    conn=_connect(db_path)
    try:
        columns=_items_columns(conn)
        selected=[x for x in _TRADE_PREVIEW_ITEM_FIELDS_12_6_3 if x in columns]
        if selected:
            sql="SELECT "+",".join('"'+x+'"' for x in selected)+" FROM items WHERE id=?"
            row=conn.execute(sql,(int(snapshot["item_id"]),)).fetchone()
            if row: snapshot.update(dict(row))
    finally: conn.close()
    return snapshot

def parse_trade_item_quantity_input(value, maximum):
    text=str(value or "").strip()
    try: quantity=int(text)
    except (TypeError,ValueError):
        return {"success":False,"reason":"invalid_quantity","message":"Введіть ціле число."}
    maximum=max(0,int(maximum or 0))
    if quantity<0 or quantity>maximum:
        return {"success":False,"reason":"quantity_out_of_range","message":f"Можна вказати від 0 до {maximum}.","maximum":maximum}
    return {"success":True,"quantity":quantity,"maximum":maximum}

def parse_trade_gold_amount_input(value, wallet_gold):
    text=str(value or "").strip().replace(",",".")
    try: amount=round(float(text),2)
    except (TypeError,ValueError):
        return {"success":False,"reason":"invalid_gold","message":"Введіть коректну суму золота."}
    wallet=round(float(wallet_gold or 0),2)
    if amount<0 or amount>wallet:
        return {"success":False,"reason":"gold_out_of_range","message":f"Можна вказати від 0 до {wallet:.2f}.","maximum":wallet}
    parts=text.split(".",1)
    if len(parts)==2 and len(parts[1])>2:
        return {"success":False,"reason":"too_many_decimals","message":"Використовуйте не більше двох знаків після крапки."}
    return {"success":True,"gold_amount":amount,"maximum":wallet}

# ROM 12.7.0 PLAYER TRADE CONFIRMATION AND ATOMIC COMMIT
PLAYER_TRADE_CONFIRM_TTL_SECONDS = 300


def _trade_side_columns_12_7_0(trade, user_id):
    uid = int(user_id)
    if uid == int(trade["initiator_user_id"]):
        return "initiator", "initiator_ready", "initiator_confirmed"
    if uid == int(trade["recipient_user_id"]):
        return "recipient", "recipient_ready", "recipient_confirmed"
    return None, None, None


def set_player_trade_ready(trade_id, user_id, ready=True, *, expected_revision=None, now=None, db_path=None):
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM player_trades WHERE id=?", (int(trade_id),)
        ).fetchone()
        if not row:
            conn.rollback()
            return {"success": False, "reason": "trade_not_found"}
        trade = dict(row)
        side, ready_col, _ = _trade_side_columns_12_7_0(trade, user_id)
        if not side:
            conn.rollback()
            return {"success": False, "reason": "wrong_actor"}
        if trade["status"] not in ("editing", "confirming"):
            conn.rollback()
            return {"success": False, "reason": "trade_not_editable"}
        if expected_revision is not None and int(expected_revision) != int(trade["revision"]):
            conn.rollback()
            return {
                "success": False,
                "reason": "stale_revision",
                "trade": trade,
            }
        value = 1 if ready else 0
        previous_value = int(trade.get(ready_col) or 0)
        changed = previous_value != value
        stamp = _text(now)
        if changed:
            conn.execute(
                f"UPDATE player_trades SET {ready_col}=?,"
                "initiator_confirmed=0,recipient_confirmed=0,updated_at=? "
                "WHERE id=?",
                (value, stamp, int(trade_id)),
            )
        updated = dict(conn.execute(
            "SELECT * FROM player_trades WHERE id=?", (int(trade_id),)
        ).fetchone())
        status = (
            "confirming"
            if int(updated["initiator_ready"]) and int(updated["recipient_ready"])
            else "editing"
        )
        expires = _text(
            _parse(stamp) + timedelta(
                seconds=(
                    PLAYER_TRADE_CONFIRM_TTL_SECONDS
                    if status == "confirming"
                    else PLAYER_TRADE_EDITING_TTL_SECONDS
                )
            )
        )
        if changed or str(updated.get("status")) != status:
            conn.execute(
                "UPDATE player_trades SET status=?,expires_at=?,updated_at=? WHERE id=?",
                (status, expires, stamp, int(trade_id)),
            )
            _trade_event(
                conn,
                int(trade_id),
                int(user_id),
                "ready_set" if value else "ready_cleared",
                int(trade["revision"]),
                stamp,
                json.dumps(
                    {"ready": bool(value), "status": status},
                    ensure_ascii=False,
                ),
            )
        conn.commit()
        updated.update({"status": status, "expires_at": expires})
        return {
            "success": True,
            "trade": updated,
            "both_ready": status == "confirming",
            "changed": changed,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def return_player_trade_to_editing(trade_id, user_id, *, expected_revision=None, now=None, db_path=None):
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM player_trades WHERE id=?", (int(trade_id),)
        ).fetchone()
        if not row:
            conn.rollback()
            return {"success": False, "reason": "trade_not_found"}
        trade = dict(row)
        side, ready_col, confirm_col = _trade_side_columns_12_7_0(trade, user_id)
        if not side:
            conn.rollback()
            return {"success": False, "reason": "wrong_actor"}
        if trade["status"] not in ("editing", "confirming"):
            conn.rollback()
            return {"success": False, "reason": "trade_not_editable"}
        # Unlocking one's own offer remains valid even if the other participant
        # changed the global revision while this participant's panel was stale.
        stamp = _text(now)
        expires = _text(
            _parse(stamp) + timedelta(seconds=PLAYER_TRADE_EDITING_TTL_SECONDS)
        )
        conn.execute(
            f"UPDATE player_trades SET status='editing',{ready_col}=0,"
            "initiator_confirmed=0,recipient_confirmed=0,updated_at=?,expires_at=? "
            "WHERE id=?",
            (stamp, expires, int(trade_id)),
        )
        _trade_event(
            conn, int(trade_id), int(user_id), "own_offer_unlocked",
            int(trade["revision"]), stamp,
            json.dumps({"side": side}, ensure_ascii=False),
        )
        conn.commit()
        return {
            "success": True,
            "trade_id": int(trade_id),
            "revision": int(trade["revision"]),
            "side": side,
            "cleared_ready_column": ready_col,
            "cleared_confirm_column": confirm_col,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _trade_commit_fail_12_7_0(conn, reason, message):
    conn.rollback(); return {"success": False, "reason": reason, "message": message}


def _trade_commit_validate_item_12_7_0(conn, trade_id, offer):
    inv = conn.execute("SELECT * FROM inventory WHERE id=? AND user_id=?", (int(offer["inventory_id"]), int(offer["owner_user_id"]))).fetchone()
    if not inv: return None, "Предмет більше не належить учаснику."
    quantity = int(offer["quantity"] or 0)
    if quantity <= 0 or int(inv["quantity"] or 0) < quantity: return None, "Кількість предмета змінилася."
    reserved = conn.execute("SELECT COALESCE(SUM(quantity),0) FROM inventory_reservations WHERE inventory_id=? AND user_id=? AND reservation_type=? AND reference_id=?", (int(offer["inventory_id"]), int(offer["owner_user_id"]), TRADE_RESERVATION_TYPE, int(trade_id))).fetchone()[0]
    if int(reserved or 0) != quantity: return None, "Резервування предмета змінилося."
    item = conn.execute("SELECT * FROM items WHERE id=?", (int(inv["item_id"]),)).fetchone()
    if not item or int(inv["item_id"]) in (501, 602, 726, 728) or str(item["category"] or "").lower() == "trash": return None, "Предмет заборонено передавати."
    equipped = conn.execute("SELECT 1 FROM equipment_slots WHERE user_id=? AND inventory_id=?", (int(offer["owner_user_id"]), int(offer["inventory_id"]))).fetchone()
    if equipped: return None, "Екіпірований предмет не можна передати."
    return (dict(inv), dict(item)), None


def _trade_stack_slots_needed_12_7_0(conn, recipient, item_id, quantity, max_stack):
    room = 0
    for row in conn.execute("SELECT quantity FROM inventory WHERE user_id=? AND item_id=?", (recipient, item_id)):
        room += max(0, max_stack - int(row[0] or 0))
    return max(0, (max(0, quantity - room) + max_stack - 1) // max_stack)


def _trade_transfer_stack_12_7_0(conn, source, recipient, quantity, item):
    inv_id = int(source["id"]); item_id = int(source["item_id"]); remaining = int(quantity); max_stack = max(1, int(item.get("max_stack") or 1))
    source_qty = int(source.get("quantity") or 0)
    conn.execute("UPDATE inventory SET quantity=quantity-? WHERE id=?", (remaining, inv_id))
    for row in conn.execute("SELECT id,quantity FROM inventory WHERE user_id=? AND item_id=? AND id<>? ORDER BY id", (recipient, item_id, inv_id)).fetchall():
        if remaining <= 0: break
        room = max(0, max_stack - int(row["quantity"] or 0)); add = min(room, remaining)
        if add: conn.execute("UPDATE inventory SET quantity=quantity+? WHERE id=?", (add, int(row["id"]))); remaining -= add
    columns = [r[1] for r in conn.execute("PRAGMA table_info(inventory)") if r[1] not in ("id", "user_id", "quantity")]
    while remaining > 0:
        add = min(max_stack, remaining); names = ["user_id", "item_id", "quantity"] + columns
        values = [recipient, item_id, add] + [source.get(name) for name in columns]
        conn.execute("INSERT INTO inventory(" + ",".join(names) + ") VALUES(" + ",".join("?" for _ in names) + ")", values); remaining -= add
    if source_qty == quantity: conn.execute("DELETE FROM inventory WHERE id=?", (inv_id,))


def _trade_offer_snapshot_12_7_0(offers, owner):
    return json.dumps([dict(x) for x in offers if int(x["owner_user_id"]) == int(owner)], ensure_ascii=False, default=str, sort_keys=True)


def _commit_player_trade_12_7_0(conn, trade, offers, stamp):
    tid = int(trade["id"]); a = int(trade["initiator_user_id"]); b = int(trade["recipient_user_id"])
    gold = {a: 0.0, b: 0.0}; validated = []
    for offer in offers:
        offer = dict(offer)
        if offer["asset_type"] == "gold": gold[int(offer["owner_user_id"])] = round(float(offer["gold_amount"] or 0), 2); continue
        pair, error = _trade_commit_validate_item_12_7_0(conn, tid, offer)
        if error: return _trade_commit_fail_12_7_0(conn, "item_validation_failed", error)
        validated.append((offer, pair[0], pair[1]))
    wallets = {int(r["user_id"]): round(float(r["gold"] or 0),2) for r in conn.execute("SELECT user_id,gold FROM users WHERE user_id IN (?,?)", (a,b))}
    if wallets.get(a,0) < gold[a] or wallets.get(b,0) < gold[b]: return _trade_commit_fail_12_7_0(conn, "insufficient_gold", "Недостатньо золота для завершення обміну.")
    # Conservative capacity check after outgoing full rows and incoming new slots.
    for recipient in (a,b):
        used = int(conn.execute("SELECT COUNT(*) FROM inventory WHERE user_id=?", (recipient,)).fetchone()[0]); cap = int(conn.execute("SELECT COALESCE(bag_slots,60) FROM users WHERE user_id=?", (recipient,)).fetchone()[0] or 60)  # ROM 17.8.1 BASE BAG CAPACITY 60
        outgoing_full = sum(1 for offer, inv, item in validated if int(offer["owner_user_id"]) == recipient and int(inv["quantity"] or 0) == int(offer["quantity"]) and int(item.get("max_stack") or 1) <= 1)
        incoming = 0
        for offer, inv, item in validated:
            if int(offer["owner_user_id"]) == recipient: continue
            if int(item.get("max_stack") or 1) <= 1: incoming += 1
            else: incoming += _trade_stack_slots_needed_12_7_0(conn, recipient, int(inv["item_id"]), int(offer["quantity"]), max(1,int(item.get("max_stack") or 1)))
        if used - outgoing_full + incoming > cap: return _trade_commit_fail_12_7_0(conn, "bag_full", "Недостатньо місця в сумці одного з учасників.")
    conn.execute("UPDATE users SET gold=ROUND(COALESCE(gold,0)-?+?,2) WHERE user_id=?", (gold[a],gold[b],a)); conn.execute("UPDATE users SET gold=ROUND(COALESCE(gold,0)-?+?,2) WHERE user_id=?", (gold[b],gold[a],b))
    for offer, inv, item in validated:
        owner=int(offer["owner_user_id"]); recipient=b if owner==a else a; quantity=int(offer["quantity"])
        if int(item.get("max_stack") or 1) <= 1:
            conn.execute("UPDATE inventory SET user_id=? WHERE id=? AND user_id=?", (recipient,int(inv["id"]),owner))
        else: _trade_transfer_stack_12_7_0(conn, inv, recipient, quantity, item)
    conn.execute("DELETE FROM inventory_reservations WHERE reservation_type=? AND reference_id=?", (TRADE_RESERVATION_TYPE,tid)); conn.execute("DELETE FROM player_activity_sessions WHERE activity_type='trade' AND reference_id=?", (str(tid),))
    conn.execute("UPDATE player_trades SET status='completed',completed_at=?,updated_at=?,expires_at=?,initiator_confirmed=1,recipient_confirmed=1 WHERE id=?", (stamp,stamp,stamp,tid))
    _trade_event(conn,tid,None,"completed",int(trade["revision"]),stamp,json.dumps({"gold":gold,"items":len(validated)},ensure_ascii=False))
    _write_trade_history(conn,trade,"completed",stamp)
    conn.execute("UPDATE player_trade_history SET initiator_offer_snapshot=?,recipient_offer_snapshot=?,summary_json=? WHERE trade_id=?", (_trade_offer_snapshot_12_7_0(offers,a),_trade_offer_snapshot_12_7_0(offers,b),json.dumps({"gold":gold,"item_offer_count":len(validated)},ensure_ascii=False),tid))
    conn.commit(); return {"success":True,"completed":True,"trade_id":tid,"initiator_user_id":a,"recipient_user_id":b,"revision":int(trade["revision"])}


def confirm_player_trade(trade_id, user_id, *, expected_revision=None, now=None, db_path=None):
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM player_trades WHERE id=?", (int(trade_id),)
        ).fetchone()
        if not row:
            return _trade_commit_fail_12_7_0(
                conn, "trade_not_found", "Обмін не знайдено."
            )
        trade = dict(row)
        side, _, confirm_col = _trade_side_columns_12_7_0(trade, user_id)
        if not side:
            return _trade_commit_fail_12_7_0(
                conn, "wrong_actor", "Немає доступу до цього обміну."
            )
        if trade["status"] == "completed":
            conn.rollback()
            return {
                "success": True,
                "completed": True,
                "idempotent": True,
                "changed": False,
                "trade_id": int(trade_id),
            }
        if (
            trade["status"] != "confirming"
            or not int(trade["initiator_ready"])
            or not int(trade["recipient_ready"])
        ):
            return _trade_commit_fail_12_7_0(
                conn, "not_ready", "Обидва учасники ще не готові."
            )
        if expected_revision is not None and int(expected_revision) != int(trade["revision"]):
            return _trade_commit_fail_12_7_0(
                conn, "stale_revision", "Пропозиція вже змінилася."
            )
        already_confirmed = bool(trade.get(confirm_col))
        stamp = _text(now)
        if not already_confirmed:
            conn.execute(
                f"UPDATE player_trades SET {confirm_col}=1,updated_at=? WHERE id=?",
                (stamp, int(trade_id)),
            )
            _trade_event(
                conn, int(trade_id), int(user_id), "final_confirmed",
                int(trade["revision"]), stamp,
            )
        trade = dict(conn.execute(
            "SELECT * FROM player_trades WHERE id=?", (int(trade_id),)
        ).fetchone())
        if not int(trade["initiator_confirmed"]) or not int(trade["recipient_confirmed"]):
            conn.commit()
            return {
                "success": True,
                "completed": False,
                "waiting": True,
                "changed": not already_confirmed,
                "trade": trade,
            }
        conn.execute(
            "UPDATE player_trades SET status='committing',updated_at=? WHERE id=?",
            (stamp, int(trade_id)),
        )
        offers = conn.execute(
            "SELECT * FROM player_trade_offers WHERE trade_id=? ORDER BY id",
            (int(trade_id),),
        ).fetchall()
        result = _commit_player_trade_12_7_0(conn, trade, offers, stamp)
        if isinstance(result, dict):
            result.setdefault("changed", not already_confirmed)
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ROM 12.6.4 PLAYER TRADE NAVIGATION LOCK AND ITEM CATEGORIES
PLAYER_TRADE_ITEM_CATEGORY_PAGE_SIZE = 8
PLAYER_TRADE_ITEM_CATEGORIES = ("equipment", "potion", "material", "rune", "consumable")


def _player_trade_item_category_12_6_4(item):
    """Return one exclusive trade UI category from canonical snapshot data."""
    item = item or {}
    snapshot = item.get("snapshot") or {}
    category = str(snapshot.get("category") or "").strip().lower()
    item_id = int(snapshot.get("item_id") or 0)

    # Explicit stack domains must win even when inventory compatibility fields
    # contain durability defaults.
    if 701 <= item_id <= 725 or category in ("rune", "runes", "stat_rune"):
        return "rune"
    if category in ("potion", "potions", "heal_potion", "mana_potion"):
        return "potion"
    if item_id == 503 or category in ("consumable", "consumables"):
        return "consumable"
    if category in ("material", "materials", "special_material", "refine_material"):
        return "material"

    if item.get("is_equipment") or _trade_offer_is_equipment_snapshot(snapshot):
        return "equipment"
    return "material"


def get_tradeable_inventory_for_trade_category(
    trade_id, user_id, category, *, page=0, page_size=8, db_path=None
):
    category = str(category or "").strip().lower()
    if category not in PLAYER_TRADE_ITEM_CATEGORIES:
        return {"success": False, "reason": "invalid_category", "items": []}
    page = max(0, int(page or 0))
    page_size = max(1, min(20, int(page_size or 8)))
    collected = []
    source_page = 0
    while source_page < 100:
        batch = get_tradeable_inventory_for_trade(
            trade_id, user_id, page=source_page, page_size=20, db_path=db_path)
        if not batch.get("success"):
            return batch
        for item in batch.get("items", []):
            if _player_trade_item_category_12_6_4(item) == category:
                enriched = dict(item)
                enriched["trade_category"] = category
                collected.append(enriched)
        if not batch.get("has_next"):
            break
        source_page += 1
    total = len(collected)
    if total == 0:
        page = 0
    elif page * page_size >= total:
        page = (total - 1) // page_size
    start = page * page_size
    return {
        "success": True,
        "trade_id": int(trade_id),
        "category": category,
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": collected[start:start + page_size],
        "has_previous": page > 0,
        "has_next": start + page_size < total,
    }


def get_player_trade_category_counts(trade_id, user_id, *, db_path=None):
    counts = {}
    for category in PLAYER_TRADE_ITEM_CATEGORIES:
        result = get_tradeable_inventory_for_trade_category(
            trade_id, user_id, category, page=0,
            page_size=PLAYER_TRADE_ITEM_CATEGORY_PAGE_SIZE, db_path=db_path)
        if not result.get("success"):
            return result
        counts[category] = int(result.get("total") or 0)
    return {"success": True, "trade_id": int(trade_id), "counts": counts}


# ROM Stage 17.31.1 canonical consumables integration
