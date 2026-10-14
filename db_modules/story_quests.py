"""Canonical persistence API for story-quest state and quest items.

All functions require an explicit SQLite connection. This keeps transaction
ownership visible to lifecycle and reward services, prevents hidden commits,
and makes exact-once operations composable in later stages.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Optional

VALID_PERSISTENT_STATUSES = frozenset({"ACTIVE", "COMPLETED", "SKIPPED"})


class StoryQuestPersistenceError(RuntimeError):
    """Base error for rejected story-quest persistence operations."""


class StoryQuestConflictError(StoryQuestPersistenceError):
    """The requested write conflicts with current persistent state."""


def utc_now_iso() -> str:
    """Return a timezone-aware UTC ISO-8601 timestamp for persistent storage."""
    return datetime.now(timezone.utc).isoformat()


def _row_dict(row: Any) -> Optional[dict[str, Any]]:
    """Normalize sqlite3.Row or tuple-free mapping rows for service consumers."""
    if row is None:
        return None
    if hasattr(row, "keys"):
        return {key: row[key] for key in row.keys()}
    raise StoryQuestPersistenceError("connection row_factory must expose mapping rows")


def _require_positive(value: int, field: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise ValueError(f"{field} must be positive")
    return parsed


def get_story_quest(connection, user_id: int, quest_id: str) -> Optional[dict[str, Any]]:
    """Return one persisted quest row without deriving LOCKED or AVAILABLE."""
    row = connection.execute(
        "SELECT * FROM user_story_quests WHERE user_id=? AND quest_id=?",
        (int(user_id), str(quest_id)),
    ).fetchone()
    return _row_dict(row)


def get_active_story_quest(connection, user_id: int) -> Optional[dict[str, Any]]:
    """Return the single ACTIVE quest guaranteed by the partial unique index."""
    row = connection.execute(
        "SELECT * FROM user_story_quests WHERE user_id=? AND status='ACTIVE'",
        (int(user_id),),
    ).fetchone()
    return _row_dict(row)


def list_story_quest_journal(connection, user_id: int) -> list[dict[str, Any]]:
    """Return materialized quest history in canonical quest-number order."""
    rows = connection.execute(
        """SELECT * FROM user_story_quests
        WHERE user_id=? ORDER BY quest_number ASC, id ASC""",
        (int(user_id),),
    ).fetchall()
    return [_row_dict(row) for row in rows]


def activate_story_quest(
    connection,
    *,
    user_id: int,
    quest_id: str,
    quest_number: int,
    target_quantity: int,
    timestamp: Optional[str] = None,
) -> dict[str, Any]:
    """Insert one ACTIVE quest without committing the caller-owned transaction.

    Repeated activation of the same already-active quest is idempotent. Any
    different existing row or another active quest is a conflict that the
    lifecycle layer must resolve explicitly.
    """
    quest_key = str(quest_id or "").strip()
    if not quest_key:
        raise ValueError("quest_id is required")
    number = _require_positive(quest_number, "quest_number")
    target = _require_positive(target_quantity, "target_quantity")
    now = str(timestamp or utc_now_iso())
    existing = get_story_quest(connection, user_id, quest_key)
    if existing is not None:
        if existing["status"] == "ACTIVE":
            return existing
        raise StoryQuestConflictError(
            f"quest {quest_key} already has persistent status {existing['status']}"
        )
    if get_active_story_quest(connection, user_id) is not None:
        raise StoryQuestConflictError("user already has an ACTIVE story quest")
    try:
        connection.execute(
            """INSERT INTO user_story_quests
            (user_id, quest_id, quest_number, status, progress, target_quantity,
             reward_claimed, started_at, updated_at)
            VALUES (?, ?, ?, 'ACTIVE', 0, ?, 0, ?, ?)""",
            (int(user_id), quest_key, number, target, now, now),
        )
    except Exception as error:
        raise StoryQuestConflictError("cannot activate story quest") from error
    return get_story_quest(connection, user_id, quest_key)


def set_story_quest_progress(
    connection,
    *,
    user_id: int,
    quest_id: str,
    progress: int,
    timestamp: Optional[str] = None,
) -> dict[str, Any]:
    """Set bounded ACTIVE progress while preserving monotonic advancement."""
    row = get_story_quest(connection, user_id, quest_id)
    if row is None or row["status"] != "ACTIVE":
        raise StoryQuestConflictError("quest is not ACTIVE")
    requested = max(0, int(progress))
    bounded = min(requested, int(row["target_quantity"]))
    if bounded < int(row["progress"]):
        raise StoryQuestConflictError("story quest progress cannot decrease")
    connection.execute(
        """UPDATE user_story_quests SET progress=?, updated_at=?
        WHERE user_id=? AND quest_id=? AND status='ACTIVE'""",
        (bounded, str(timestamp or utc_now_iso()), int(user_id), str(quest_id)),
    )
    return get_story_quest(connection, user_id, quest_id)


def get_story_quest_item_quantity(
    connection, user_id: int, quest_id: str, item_key: str
) -> int:
    """Return an isolated quest-item quantity without reading ordinary inventory."""
    row = connection.execute(
        """SELECT quantity FROM user_story_quest_items
        WHERE user_id=? AND quest_id=? AND item_key=?""",
        (int(user_id), str(quest_id), str(item_key)),
    ).fetchone()
    return int(row[0]) if row else 0


def get_total_story_quest_item_quantity(connection, user_id: int, item_key: str) -> int:
    """Return one clue quantity across source quests for later retained turn-ins."""
    row = connection.execute(
        """SELECT COALESCE(SUM(quantity),0) FROM user_story_quest_items
        WHERE user_id=? AND item_key=?""",
        (int(user_id), str(item_key)),
    ).fetchone()
    return max(0, int(row[0] or 0)) if row else 0


def consume_story_quest_item_quantity(
    connection, *, user_id: int, item_key: str, quantity: int
) -> int:
    """Consume an exact quantity across retained source rows, oldest first.

    The caller owns the surrounding transaction. Any insufficient or concurrent
    state raises before completion, allowing the outer transaction to roll back
    every row and the reward/status mutation together.
    """
    required = int(quantity)
    if required <= 0:
        raise StoryQuestPersistenceError("consume quantity must be positive")
    rows = connection.execute(
        """SELECT quest_id, quantity FROM user_story_quest_items
        WHERE user_id=? AND item_key=? AND quantity>0
        ORDER BY updated_at, quest_id""",
        (int(user_id), str(item_key)),
    ).fetchall()
    if sum(int(row[1] or 0) for row in rows) < required:
        raise StoryQuestConflictError("required quest item quantity is incomplete")
    remaining = required
    for quest_id, current_raw in rows:
        current = int(current_raw or 0)
        take = min(current, remaining)
        if take <= 0:
            continue
        if take == current:
            changed = connection.execute(
                """DELETE FROM user_story_quest_items
                WHERE user_id=? AND quest_id=? AND item_key=? AND quantity=?""",
                (int(user_id), str(quest_id), str(item_key), current),
            )
        else:
            changed = connection.execute(
                """UPDATE user_story_quest_items SET quantity=quantity-?, updated_at=?
                WHERE user_id=? AND quest_id=? AND item_key=? AND quantity=?""",
                (take, utc_now_iso(), int(user_id), str(quest_id), str(item_key), current),
            )
        if changed.rowcount != 1:
            raise StoryQuestConflictError("quest item quantity changed concurrently")
        remaining -= take
        if remaining == 0:
            break
    return required


def add_story_quest_item(
    connection,
    *,
    user_id: int,
    quest_id: str,
    item_key: str,
    quantity: int,
    required_quantity: int,
    timestamp: Optional[str] = None,
) -> dict[str, Any]:
    """Grant a bounded quest-item quantity only to the matching ACTIVE quest.

    The operation never touches ordinary inventory and returns both the amount
    actually granted and the resulting quantity for user-visible progress.
    """
    delta = _require_positive(quantity, "quantity")
    limit = _require_positive(required_quantity, "required_quantity")
    key = str(item_key or "").strip()
    if not key:
        raise ValueError("item_key is required")
    quest = get_story_quest(connection, user_id, quest_id)
    if quest is None or quest["status"] != "ACTIVE":
        raise StoryQuestConflictError("quest is not ACTIVE")
    current = get_story_quest_item_quantity(connection, user_id, quest_id, key)
    resulting = min(limit, current + delta)
    granted = resulting - current
    if granted > 0:
        connection.execute(
            """INSERT INTO user_story_quest_items
            (user_id, quest_id, item_key, quantity, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, quest_id, item_key) DO UPDATE SET
                quantity=excluded.quantity,
                updated_at=excluded.updated_at""",
            (int(user_id), str(quest_id), key, resulting,
             str(timestamp or utc_now_iso())),
        )
    return {"granted": granted, "quantity": resulting, "required_quantity": limit}


def reconcile_story_location_as_skipped(
    connection,
    *,
    user_id: int,
    quests,
    timestamp: Optional[str] = None,
) -> dict[str, Any]:
    """Persist every unfinished quest in one exceeded location as SKIPPED.

    Existing COMPLETED rows remain authoritative. Existing SKIPPED rows are
    idempotent. ACTIVE rows and not-yet-materialized AVAILABLE/LOCKED quests are
    finalized without rewards; isolated quest-item rows for the location are
    removed by the caller-owned transaction.
    """
    ordered = sorted(tuple(quests), key=lambda quest: int(quest.number))
    now = str(timestamp or utc_now_iso())
    completed = skipped_now = already_skipped = 0
    quest_ids = []
    for quest in ordered:
        quest_id = str(quest.quest_id); quest_ids.append(quest_id)
        row = get_story_quest(connection, int(user_id), quest_id)
        if row is not None and str(row["status"]) == "COMPLETED":
            completed += 1
            continue
        if row is not None and str(row["status"]) == "SKIPPED":
            already_skipped += 1
            continue
        if row is not None:
            updated = connection.execute(
                """UPDATE user_story_quests
                SET status='SKIPPED', reward_claimed=0, skipped_at=?,
                    completed_at=NULL, updated_at=?
                WHERE user_id=? AND quest_id=? AND status='ACTIVE'""",
                (now, now, int(user_id), quest_id),
            )
            if updated.rowcount != 1:
                raise StoryQuestConflictError("story quest changed concurrently")
        else:
            connection.execute(
                """INSERT INTO user_story_quests
                (user_id, quest_id, quest_number, status, progress,
                 target_quantity, reward_claimed, started_at, completed_at,
                 skipped_at, updated_at)
                VALUES (?, ?, ?, 'SKIPPED', 0, ?, 0, ?, NULL, ?, ?)""",
                (int(user_id), quest_id, int(quest.number),
                 int(quest.target_quantity), now, now, now),
            )
        skipped_now += 1
    if quest_ids:
        placeholders = ",".join("?" for _ in quest_ids)
        connection.execute(
            f"DELETE FROM user_story_quest_items WHERE user_id=? AND quest_id IN ({placeholders})",
            (int(user_id), *quest_ids),
        )
    return {"completed": completed, "skipped_now": skipped_now,
            "already_skipped": already_skipped, "quest_count": len(ordered)}


def skip_active_story_quest(
    connection,
    *,
    user_id: int,
    quest_id: str,
    timestamp: Optional[str] = None,
) -> dict[str, Any]:
    """Mark one ACTIVE quest SKIPPED and remove only its isolated quest items.

    The caller owns commit or rollback, so status and item cleanup can remain in
    the same transaction as the future over-level lifecycle operation.
    """
    row = get_story_quest(connection, user_id, quest_id)
    if row is None or row["status"] != "ACTIVE":
        raise StoryQuestConflictError("quest is not ACTIVE")
    now = str(timestamp or utc_now_iso())
    updated = connection.execute(
        """UPDATE user_story_quests
        SET status='SKIPPED', skipped_at=?, updated_at=?
        WHERE user_id=? AND quest_id=? AND status='ACTIVE'""",
        (now, now, int(user_id), str(quest_id)),
    )
    if updated.rowcount != 1:
        raise StoryQuestConflictError("ACTIVE quest changed concurrently")
    connection.execute(
        "DELETE FROM user_story_quest_items WHERE user_id=? AND quest_id=?",
        (int(user_id), str(quest_id)),
    )
    return get_story_quest(connection, user_id, quest_id)
