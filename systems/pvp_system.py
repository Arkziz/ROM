from __future__ import annotations

import inspect
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

PVP_ACTION_TIMEOUT_SECONDS = 20
PVP_MAX_ROUNDS = 50
PVP_CONSECUTIVE_AFK_LIMIT = 5
PVP_ACTIVE_STATUSES = ("waiting", "active", "resolving")
PVP_TERMINAL_STATUSES = ("completed", "cancelled", "expired")

ConnectionFactory = Callable[[], sqlite3.Connection]
_CONNECTION_FACTORY: ConnectionFactory | None = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None = None) -> str:
    return (value or _utc_now()).astimezone(timezone.utc).isoformat(timespec="seconds")


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


def configure_pvp_connection_factory(factory: ConnectionFactory | None) -> None:
    global _CONNECTION_FACTORY
    _CONNECTION_FACTORY = factory


def _default_connection() -> sqlite3.Connection:
    try:
        import db as db_module
    except ImportError:
        db_module = None
    if db_module is not None:
        for name in ("get_db_connection", "get_connection", "connect_db", "create_connection"):
            candidate = getattr(db_module, name, None)
            if callable(candidate):
                connection = candidate()
                connection.row_factory = sqlite3.Row
                return connection
        declared_path = getattr(db_module, "DB_PATH", None)
        if declared_path:
            connection = sqlite3.connect(str(declared_path), timeout=30)
            connection.row_factory = sqlite3.Row
            return connection
    root = Path(__file__).resolve().parents[1]
    connection = sqlite3.connect(str(root / "game.db"), timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def _connection(connection: sqlite3.Connection | None = None):
    owned = connection is None
    conn = connection or (_CONNECTION_FACTORY() if _CONNECTION_FACTORY else _default_connection())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        if owned:
            conn.close()


def init_pvp_foundation(connection: sqlite3.Connection | None = None) -> dict[str, Any]:
    with _connection(connection) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS pvp_battles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                challenger_id INTEGER NOT NULL,
                opponent_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'waiting'
                    CHECK(status IN ('waiting','active','resolving','completed','cancelled','expired')),
                round_number INTEGER NOT NULL DEFAULT 1 CHECK(round_number >= 1),
                revision INTEGER NOT NULL DEFAULT 1 CHECK(revision >= 1),
                resolving INTEGER NOT NULL DEFAULT 0 CHECK(resolving IN (0,1)),
                action_deadline TEXT,
                winner_id INTEGER,
                result_reason TEXT,
                max_rounds INTEGER NOT NULL DEFAULT 50 CHECK(max_rounds >= 1),
                action_timeout_seconds INTEGER NOT NULL DEFAULT 20 CHECK(action_timeout_seconds >= 1),
                state_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                CHECK(challenger_id <> opponent_id)
            );

            CREATE TABLE IF NOT EXISTS pvp_participants (
                battle_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                side TEXT NOT NULL CHECK(side IN ('challenger','opponent')),
                class_key TEXT NOT NULL,
                max_hp INTEGER NOT NULL CHECK(max_hp >= 1),
                hp INTEGER NOT NULL CHECK(hp >= 0),
                max_mp INTEGER NOT NULL DEFAULT 0 CHECK(max_mp >= 0),
                mp INTEGER NOT NULL DEFAULT 0 CHECK(mp >= 0),
                resource_type TEXT NOT NULL,
                resource_value INTEGER NOT NULL DEFAULT 0,
                combo INTEGER NOT NULL DEFAULT 0 CHECK(combo >= 0),
                consecutive_afk INTEGER NOT NULL DEFAULT 0 CHECK(consecutive_afk >= 0),
                stunned_next INTEGER NOT NULL DEFAULT 0 CHECK(stunned_next IN (0,1)),
                cooldowns_json TEXT NOT NULL DEFAULT '{}',
                effects_json TEXT NOT NULL DEFAULT '{}',
                snapshot_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (battle_id, user_id),
                UNIQUE (battle_id, side),
                FOREIGN KEY (battle_id) REFERENCES pvp_battles(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS pvp_round_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                battle_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL CHECK(round_number >= 1),
                revision INTEGER NOT NULL CHECK(revision >= 1),
                user_id INTEGER NOT NULL,
                action_type TEXT NOT NULL CHECK(action_type IN ('basic_attack','skill','afk_skip','stunned_skip')),
                skill_key TEXT,
                payload_json TEXT NOT NULL DEFAULT '{}',
                submitted_at TEXT NOT NULL,
                UNIQUE (battle_id, round_number, user_id),
                FOREIGN KEY (battle_id) REFERENCES pvp_battles(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS pvp_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                battle_id INTEGER NOT NULL,
                round_number INTEGER,
                revision INTEGER,
                event_type TEXT NOT NULL,
                actor_id INTEGER,
                target_id INTEGER,
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (battle_id) REFERENCES pvp_battles(id) ON DELETE CASCADE
            );

            CREATE UNIQUE INDEX IF NOT EXISTS ux_pvp_request_once
                ON pvp_battles(request_id) WHERE request_id IS NOT NULL;
            CREATE INDEX IF NOT EXISTS ix_pvp_battles_status_deadline
                ON pvp_battles(status, action_deadline);
            CREATE INDEX IF NOT EXISTS ix_pvp_battles_challenger_status
                ON pvp_battles(challenger_id, status);
            CREATE INDEX IF NOT EXISTS ix_pvp_battles_opponent_status
                ON pvp_battles(opponent_id, status);
            CREATE INDEX IF NOT EXISTS ix_pvp_actions_round
                ON pvp_round_actions(battle_id, round_number, revision);
            CREATE INDEX IF NOT EXISTS ix_pvp_events_battle
                ON pvp_events(battle_id, id);
            """
        )
        conn.commit()
        return {
            "tables": ["pvp_battles", "pvp_participants", "pvp_round_actions", "pvp_events"],
            "action_timeout_seconds": PVP_ACTION_TIMEOUT_SECONDS,
            "maximum_rounds": PVP_MAX_ROUNDS,
            "afk_limit": PVP_CONSECUTIVE_AFK_LIMIT,
        }


def _row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def get_pvp_battle(battle_id: int, connection: sqlite3.Connection | None = None) -> dict[str, Any] | None:
    with _connection(connection) as conn:
        row = conn.execute("SELECT * FROM pvp_battles WHERE id = ?", (int(battle_id),)).fetchone()
        result = _row_dict(row)
        if result:
            result["state"] = _loads(result.pop("state_json", None), {})
        return result


def get_pvp_participants(battle_id: int, connection: sqlite3.Connection | None = None) -> list[dict[str, Any]]:
    with _connection(connection) as conn:
        rows = conn.execute(
            "SELECT * FROM pvp_participants WHERE battle_id = ? ORDER BY side",
            (int(battle_id),),
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["cooldowns"] = _loads(item.pop("cooldowns_json", None), {})
            item["effects"] = _loads(item.pop("effects_json", None), {})
            item["snapshot"] = _loads(item.pop("snapshot_json", None), {})
            result.append(item)
        return result


def _normalized_participant(user_id: int, side: str, snapshot: Mapping[str, Any], now: str) -> tuple[Any, ...]:
    class_key = str(snapshot.get("class_key") or snapshot.get("character_class") or "").strip().lower()
    if not class_key:
        raise ValueError("participant class_key is required")
    max_hp = max(1, int(snapshot.get("max_hp") or 1))
    max_mp = max(0, int(snapshot.get("max_mp") or 0))
    resource_type = str(snapshot.get("resource_type") or "rage")
    resource_value = 100 if resource_type in {"combat_energy", "combat_energy_combo"} else 0
    if resource_type == "mana":
        resource_value = max_mp
    return (
        int(user_id), side, class_key, max_hp, max_hp, max_mp, max_mp,
        resource_type, resource_value, 0, 0, 0, "{}", "{}", _json(dict(snapshot)), now, now,
    )


def create_pvp_battle(
    challenger_id: int,
    opponent_id: int,
    challenger_snapshot: Mapping[str, Any],
    opponent_snapshot: Mapping[str, Any],
    request_id: int | None = None,
    start_immediately: bool = True,
    now: datetime | None = None,
    connection: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    challenger_id = int(challenger_id)
    opponent_id = int(opponent_id)
    if challenger_id == opponent_id:
        raise ValueError("self duel is forbidden")
    moment = now or _utc_now()
    now_text = _iso(moment)
    deadline = _iso(moment + timedelta(seconds=PVP_ACTION_TIMEOUT_SECONDS)) if start_immediately else None
    status = "active" if start_immediately else "waiting"
    with _connection(connection) as conn:
        init_pvp_foundation(conn)
        conn.execute("BEGIN IMMEDIATE")
        try:
            conflict = conn.execute(
                """
                SELECT id FROM pvp_battles
                WHERE status IN ('waiting','active','resolving')
                  AND (challenger_id IN (?, ?) OR opponent_id IN (?, ?))
                LIMIT 1
                """,
                (challenger_id, opponent_id, challenger_id, opponent_id),
            ).fetchone()
            if conflict:
                raise ValueError("one of the players is already in an active PvP battle")
            cursor = conn.execute(
                """
                INSERT INTO pvp_battles(
                    request_id, challenger_id, opponent_id, status, round_number, revision,
                    resolving, action_deadline, max_rounds, action_timeout_seconds,
                    state_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 1, 1, 0, ?, ?, ?, '{}', ?, ?)
                """,
                (
                    request_id, challenger_id, opponent_id, status, deadline,
                    PVP_MAX_ROUNDS, PVP_ACTION_TIMEOUT_SECONDS, now_text, now_text,
                ),
            )
            battle_id = int(cursor.lastrowid)
            sql = """
                INSERT INTO pvp_participants(
                    battle_id, user_id, side, class_key, max_hp, hp, max_mp, mp,
                    resource_type, resource_value, combo, consecutive_afk, stunned_next,
                    cooldowns_json, effects_json, snapshot_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            conn.execute(sql, (battle_id,) + _normalized_participant(challenger_id, "challenger", challenger_snapshot, now_text))
            conn.execute(sql, (battle_id,) + _normalized_participant(opponent_id, "opponent", opponent_snapshot, now_text))
            add_pvp_event(battle_id, "battle_created", payload={"status": status}, connection=conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        battle = get_pvp_battle(battle_id, conn)
        participants = get_pvp_participants(battle_id, conn)
        return {"battle": battle, "participants": participants}


def add_pvp_event(
    battle_id: int,
    event_type: str,
    round_number: int | None = None,
    revision: int | None = None,
    actor_id: int | None = None,
    target_id: int | None = None,
    payload: Mapping[str, Any] | None = None,
    connection: sqlite3.Connection | None = None,
) -> int:
    with _connection(connection) as conn:
        cursor = conn.execute(
            """
            INSERT INTO pvp_events(
                battle_id, round_number, revision, event_type, actor_id, target_id, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (int(battle_id), round_number, revision, str(event_type), actor_id, target_id, _json(dict(payload or {})), _iso()),
        )
        if connection is None:
            conn.commit()
        return int(cursor.lastrowid)


def submit_pvp_action(
    battle_id: int,
    user_id: int,
    round_number: int,
    revision: int,
    action_type: str,
    skill_key: str | None = None,
    payload: Mapping[str, Any] | None = None,
    connection: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    if action_type not in {"basic_attack", "skill", "afk_skip", "stunned_skip"}:
        raise ValueError("unsupported PvP action type")
    if action_type == "skill" and not skill_key:
        raise ValueError("skill_key is required for skill action")
    with _connection(connection) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            battle = conn.execute("SELECT * FROM pvp_battles WHERE id = ?", (int(battle_id),)).fetchone()
            if not battle or battle["status"] != "active":
                raise ValueError("PvP battle is not active")
            if int(battle["round_number"]) != int(round_number) or int(battle["revision"]) != int(revision):
                raise ValueError("stale PvP callback")
            participant = conn.execute(
                "SELECT 1 FROM pvp_participants WHERE battle_id = ? AND user_id = ?",
                (int(battle_id), int(user_id)),
            ).fetchone()
            if not participant:
                raise ValueError("actor does not belong to this PvP battle")
            conn.execute(
                """
                INSERT INTO pvp_round_actions(
                    battle_id, round_number, revision, user_id, action_type, skill_key, payload_json, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (int(battle_id), int(round_number), int(revision), int(user_id), action_type, skill_key, _json(dict(payload or {})), _iso()),
            )
            count = conn.execute(
                "SELECT COUNT(*) FROM pvp_round_actions WHERE battle_id = ? AND round_number = ? AND revision = ?",
                (int(battle_id), int(round_number), int(revision)),
            ).fetchone()[0]
            add_pvp_event(
                int(battle_id), "action_submitted", int(round_number), int(revision), int(user_id),
                payload={"action_type": action_type, "skill_key": skill_key}, connection=conn,
            )
            conn.commit()
            return {"accepted": True, "actions_ready": int(count), "both_ready": int(count) >= 2}
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            raise ValueError("action already submitted for this round") from exc
        except Exception:
            conn.rollback()
            raise


def get_pvp_round_actions(
    battle_id: int,
    round_number: int,
    revision: int,
    connection: sqlite3.Connection | None = None,
) -> list[dict[str, Any]]:
    with _connection(connection) as conn:
        rows = conn.execute(
            """
            SELECT * FROM pvp_round_actions
            WHERE battle_id = ? AND round_number = ? AND revision = ?
            ORDER BY user_id
            """,
            (int(battle_id), int(round_number), int(revision)),
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["payload"] = _loads(item.pop("payload_json", None), {})
            result.append(item)
        return result


def claim_pvp_round_resolution(
    battle_id: int,
    round_number: int,
    revision: int,
    connection: sqlite3.Connection | None = None,
) -> bool:
    with _connection(connection) as conn:
        cursor = conn.execute(
            """
            UPDATE pvp_battles
               SET resolving = 1, status = 'resolving', updated_at = ?
             WHERE id = ? AND status = 'active' AND resolving = 0
               AND round_number = ? AND revision = ?
            """,
            (_iso(), int(battle_id), int(round_number), int(revision)),
        )
        conn.commit()
        return cursor.rowcount == 1


def release_pvp_round_resolution(
    battle_id: int,
    expected_revision: int,
    next_deadline: datetime | None = None,
    connection: sqlite3.Connection | None = None,
) -> bool:
    deadline = _iso(next_deadline or (_utc_now() + timedelta(seconds=PVP_ACTION_TIMEOUT_SECONDS)))
    with _connection(connection) as conn:
        cursor = conn.execute(
            """
            UPDATE pvp_battles
               SET status = 'active', resolving = 0,
                   round_number = round_number + 1,
                   revision = revision + 1,
                   action_deadline = ?, updated_at = ?
             WHERE id = ? AND status = 'resolving' AND resolving = 1 AND revision = ?
            """,
            (deadline, _iso(), int(battle_id), int(expected_revision)),
        )
        conn.commit()
        return cursor.rowcount == 1


def complete_pvp_battle(
    battle_id: int,
    result_reason: str,
    winner_id: int | None = None,
    status: str = "completed",
    connection: sqlite3.Connection | None = None,
) -> bool:
    if status not in PVP_TERMINAL_STATUSES:
        raise ValueError("invalid terminal PvP status")
    with _connection(connection) as conn:
        cursor = conn.execute(
            """
            UPDATE pvp_battles
               SET status = ?, resolving = 0, action_deadline = NULL,
                   winner_id = ?, result_reason = ?, completed_at = ?, updated_at = ?
             WHERE id = ? AND status IN ('waiting','active','resolving')
            """,
            (status, winner_id, str(result_reason), _iso(), _iso(), int(battle_id)),
        )
        if cursor.rowcount:
            add_pvp_event(int(battle_id), "battle_finished", payload={"status": status, "reason": result_reason, "winner_id": winner_id}, connection=conn)
        conn.commit()
        return cursor.rowcount == 1


def get_pvp_recovery_plan(
    now: datetime | None = None,
    connection: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    moment = now or _utc_now()
    with _connection(connection) as conn:
        rows = conn.execute(
            "SELECT * FROM pvp_battles WHERE status IN ('waiting','active','resolving') ORDER BY id"
        ).fetchall()
        active = []
        expired = []
        resolving = []
        for row in rows:
            item = dict(row)
            deadline = _parse(item.get("action_deadline"))
            if item["status"] == "resolving":
                resolving.append(item["id"])
            elif deadline is not None and deadline <= moment:
                expired.append(item["id"])
            else:
                active.append(item["id"])
        return {"active": active, "expired": expired, "resolving": resolving}


def recover_pvp_after_restart(
    now: datetime | None = None,
    connection: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    """Return a persisted recovery plan; Stage 14.4/14.5 will attach timers and AFK resolution."""
    with _connection(connection) as conn:
        init_pvp_foundation(conn)
        plan = get_pvp_recovery_plan(now=now, connection=conn)
        for battle_id in plan["resolving"]:
            conn.execute(
                """
                UPDATE pvp_battles
                   SET status = 'active', resolving = 0, revision = revision + 1, updated_at = ?
                 WHERE id = ? AND status = 'resolving'
                """,
                (_iso(now or _utc_now()), int(battle_id)),
            )
            add_pvp_event(int(battle_id), "restart_resolution_released", payload={}, connection=conn)
        conn.commit()
        plan["released_resolving"] = list(plan["resolving"])
        return plan


def get_pvp_events(battle_id: int, connection: sqlite3.Connection | None = None) -> list[dict[str, Any]]:
    with _connection(connection) as conn:
        rows = conn.execute("SELECT * FROM pvp_events WHERE battle_id = ? ORDER BY id", (int(battle_id),)).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["payload"] = _loads(item.pop("payload_json", None), {})
            result.append(item)
        return result
