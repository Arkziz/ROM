from __future__ import annotations

from typing import Any, Mapping

from systems.player_interaction_system import release_player_activity_session
from systems.pvp_system import complete_pvp_battle, get_pvp_battle, get_pvp_participants

TERMINAL_STATUSES = frozenset(("completed", "cancelled", "expired"))

_REASON_TEXT = {
    "hp_zero": "перемога в бою",
    "terminal": "перемога в бою",
    "simultaneous": "перемога в бою",
    "periodic": "перемога в бою",
    "draw_periodic": "обидва персонажі одночасно втратили все здоров’я",
    "draw_simultaneous": "обидва персонажі одночасно втратили все здоров’я",
    "technical_draw_both_afk": "обидва учасники пропустили 5 ходів поспіль",
    "afk_defeat": "5 пропущених ходів поспіль",
    "afk_limit": "5 пропущених ходів поспіль",
    "surrender": "один з учасників здався",
    "technical_cancel": "дуель завершено через технічну помилку",
    "server_restart_cancel": "дуель скасовано після перезапуску сервера",
    "activity_session_acquire_failed": "не вдалося розпочати дуель",
}


def _name(participant: Mapping[str, Any] | None, fallback: str) -> str:
    row = dict(participant or {})
    snapshot = dict(row.get("snapshot") or {})
    return str(snapshot.get("character_name") or row.get("character_name") or fallback)


def _participants_by_id(battle_id: int) -> dict[int, dict[str, Any]]:
    return {int(row["user_id"]): dict(row) for row in get_pvp_participants(int(battle_id))}


def release_pvp_activity_sessions(battle_id: int) -> dict[str, Any]:
    released = 0
    participants = list(get_pvp_participants(int(battle_id)))
    for row in participants:
        result = release_player_activity_session(
            int(row["user_id"]), activity_type="pvp_battle", reference_id=int(battle_id)
        )
        released += int(result.get("released") or 0)
    return {"success": True, "participants": len(participants), "released": released}


def complete_pvp_battle_once(battle_id: int, result_reason: str, winner_id: int | None = None, *, status: str = "completed") -> dict[str, Any]:
    before = get_pvp_battle(int(battle_id))
    if not before:
        return {"success": False, "reason": "battle_not_found"}
    already_terminal = str(before.get("status") or "") in TERMINAL_STATUSES
    changed = False
    if not already_terminal:
        changed = bool(complete_pvp_battle(int(battle_id), str(result_reason), int(winner_id) if winner_id is not None else None, status=str(status)))
    after = get_pvp_battle(int(battle_id)) or before
    cleanup = release_pvp_activity_sessions(int(battle_id))
    return {"success": str(after.get("status") or "") in TERMINAL_STATUSES, "changed": changed, "already_terminal": already_terminal, "battle": after, "cleanup": cleanup}


def surrender_pvp_battle(battle_id: int, user_id: int, expected_revision: int) -> dict[str, Any]:
    battle = get_pvp_battle(int(battle_id))
    if not battle:
        return {"success": False, "reason": "battle_not_found"}
    if str(battle.get("status") or "") not in {"waiting", "active", "resolving"}:
        return {"success": False, "reason": "battle_already_finished", "battle": battle}
    if int(battle.get("revision") or 0) != int(expected_revision):
        return {"success": False, "reason": "stale_revision", "battle": battle}
    participants = _participants_by_id(int(battle_id))
    uid = int(user_id)
    if uid not in participants or len(participants) != 2:
        return {"success": False, "reason": "wrong_actor"}
    winner_id = next(pid for pid in participants if pid != uid)
    result = complete_pvp_battle_once(int(battle_id), "surrender", winner_id)
    result.update({"loser_id": uid, "winner_id": winner_id})
    return result


def render_pvp_terminal_text(battle_id: int, viewer_id: int) -> str:
    battle = get_pvp_battle(int(battle_id)) or {}
    participants = _participants_by_id(int(battle_id))
    viewer_id = int(viewer_id)
    winner_id = battle.get("winner_id")
    reason = str(battle.get("result_reason") or "terminal")
    reason_text = _REASON_TEXT.get(reason, "дуель завершено")
    viewer = participants.get(viewer_id)
    opponent = next((row for uid, row in participants.items() if uid != viewer_id), None)
    viewer_name = _name(viewer, f"Гравець #{viewer_id}")
    opponent_name = _name(opponent, "Суперник")
    if winner_id is None:
        return "🤝 <b>Дуель завершилася нічиєю.</b>\n\n" + f"Учасники: {viewer_name} та {opponent_name}.\nПричина: {reason_text}."
    if int(winner_id) == viewer_id:
        return "🏆 <b>Перемога в дуелі!</b>\n\n" + f"Переможець: {viewer_name}.\nПричина: {reason_text}."
    winner_name = _name(participants.get(int(winner_id)), opponent_name)
    return "💀 <b>Поразка в дуелі.</b>\n\n" + f"Переможець: {winner_name}.\nПричина: {reason_text}."


def cleanup_all_terminal_pvp_sessions() -> dict[str, Any]:
    from systems.pvp_system import cleanup_terminal_pvp_activity_sessions
    return cleanup_terminal_pvp_activity_sessions()
