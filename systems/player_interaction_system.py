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
            _trade_event(conn,trade["id"],None,"expired",trade["revision"],stamp,'{}')
            _write_trade_history(conn,trade,"expired",stamp,"timeout")
        conn.commit(); return len(rows)
    except Exception:
        conn.rollback(); raise
    finally: conn.close()

