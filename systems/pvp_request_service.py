from __future__ import annotations

from typing import Any, Callable

from systems.player_interaction_system import (
    create_player_interaction_request,
    get_interaction_request,
    respond_to_player_interaction_request,
)

PVP_DUEL_REQUEST_TTL_SECONDS = 120


def create_pvp_duel_request(initiator_user_id: int, recipient_user_id: int, *, pve_busy_checker=None, now=None, db_path=None) -> dict[str, Any]:
    return create_player_interaction_request(
        int(initiator_user_id), int(recipient_user_id), "duel",
        ttl_seconds=PVP_DUEL_REQUEST_TTL_SECONDS,
        pve_busy_checker=pve_busy_checker, now=now, db_path=db_path,
    )


def respond_to_pvp_duel_request(request_id: int, actor_user_id: int, action: str, *, expected_revision: int = 1, pve_busy_checker=None, now=None, db_path=None) -> dict[str, Any]:
    request = get_interaction_request(int(request_id), db_path=db_path)
    if not request or request.get("request_type") != "duel":
        return {"success": False, "reason": "request_not_found"}
    return respond_to_player_interaction_request(
        int(request_id), int(actor_user_id), str(action),
        expected_revision=int(expected_revision), pve_busy_checker=pve_busy_checker,
        now=now, db_path=db_path,
    )



def cancel_failed_accepted_pvp_duel_request(request_id: int, *, db_path=None) -> dict[str, Any]:
    """Convert an accepted request with no battle into cancelled, allowing a clean retry."""
    from systems import player_interaction_system as interaction
    connection = interaction._connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT status,request_type FROM player_interaction_requests WHERE id=?",
            (int(request_id),),
        ).fetchone()
        if not row or row["request_type"] != "duel":
            connection.rollback(); return {"success": False, "reason": "request_not_found"}
        if row["status"] == "accepted":
            connection.execute(
                "UPDATE player_interaction_requests SET status='cancelled',revision=revision+1,updated_at=datetime('now'),responded_at=datetime('now') WHERE id=?",
                (int(request_id),),
            )
        connection.execute(
            "DELETE FROM player_activity_sessions WHERE reference_id=? AND activity_type IN ('duel_request','pvp_battle')",
            (int(request_id),),
        )
        connection.commit(); return {"success": True, "status": "cancelled"}
    except Exception:
        connection.rollback(); raise
    finally:
        connection.close()
