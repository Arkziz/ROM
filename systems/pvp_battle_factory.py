from __future__ import annotations

import logging
from typing import Any, Callable, Mapping

from data.classes import CLASS_CONFIGS
from systems.player_interaction_system import (
    acquire_player_activity_session,
    release_player_activity_session,
)
from systems.pvp_system import complete_pvp_battle, create_pvp_battle, init_pvp_foundation

LOGGER = logging.getLogger(__name__)
SnapshotProvider = Callable[[int], Mapping[str, Any]]


def _call(module, name: str, user_id: int, default: Any = 0) -> Any:
    function = getattr(module, name, None)
    if not callable(function):
        return default
    value = function(int(user_id))
    return default if value is None else value


def _coerce_current_mp(value: Any, fallback: int = 0) -> int:
    """Normalize the public ROM MP contract without changing db.get_user_mp().

    The canonical public function returns a mapping with mp/max_mp/current_mp, while
    older isolated fixtures may return a numeric value. PvP accepts both contracts.
    """
    if isinstance(value, Mapping):
        value = value.get("mp", value.get("current_mp", fallback))
    try:
        return max(0, int(value if value is not None else fallback))
    except (TypeError, ValueError):
        return max(0, int(fallback or 0))


def build_production_pvp_snapshot(user_id: int) -> dict[str, Any]:
    """Build and validate the immutable snapshot before accepting a request."""
    import db

    uid = int(user_id)
    class_key = str(_call(db, "get_character_class", uid, "") or "").strip().lower()
    if class_key not in CLASS_CONFIGS:
        raise ValueError(f"unsupported_character_class:{class_key or 'missing'}")
    resource_type = str(CLASS_CONFIGS[class_key].get("resource") or _call(db, "get_character_resource_type", uid, "rage"))
    max_hp = max(1, int(_call(db, "get_max_hp", uid, 1)))
    max_mp = max(0, int(_call(db, "get_max_mp", uid, 0)))
    attack_profile = _call(db, "get_player_attack_profile", uid, {}) or {}
    attack_type = str(attack_profile.get("attack_type") or "physical")
    weapon_min = float(attack_profile.get("weapon_min_damage") or 0)
    weapon_max = float(attack_profile.get("weapon_max_damage") or 0)
    return {
        "class_key": class_key,
        "level": max(1, int(_call(db, "get_player_level", uid, 1))),
        "max_hp": max_hp,
        "max_mp": max_mp,
        "resource_type": resource_type,
        "physical_attack": float(_call(db, "get_attack", uid, 0)),
        "magical_attack": float(_call(db, "get_magic_attack", uid, 0)),
        "physical_defense": float(_call(db, "get_physical_defense", uid, 0)),
        "magical_defense": float(_call(db, "get_magic_defense", uid, 0)),
        "physical_crit_chance": float(_call(db, "get_physical_crit_chance_display", uid, 0)),
        "magical_crit_chance": float(_call(db, "get_magical_crit_chance_display", uid, 0)),
        "dodge_chance": float(_call(db, "get_base_dodge_chance_display", uid, 0)),
        "weapon_physical_min": weapon_min if attack_type == "physical" else 0.0,
        "weapon_physical_max": weapon_max if attack_type == "physical" else 0.0,
        "weapon_magical_min": weapon_min if attack_type == "magical" else 0.0,
        "weapon_magical_max": weapon_max if attack_type == "magical" else 0.0,
        "production_hp": int(_call(db, "get_current_hp", uid, max_hp)),
        "production_mp": _coerce_current_mp(_call(db, "get_user_mp", uid, {"mp": max_mp}), max_mp),
    }


def prepare_pvp_duel_snapshots(initiator_user_id: int, recipient_user_id: int, *, snapshot_provider: SnapshotProvider | None = None) -> dict[str, Any]:
    provider = snapshot_provider or build_production_pvp_snapshot
    try:
        return {
            "success": True,
            "initiator_snapshot": dict(provider(int(initiator_user_id))),
            "recipient_snapshot": dict(provider(int(recipient_user_id))),
        }
    except Exception as exc:
        LOGGER.exception("PvP snapshot preparation failed")
        return {"success": False, "reason": "pvp_snapshot_failed", "error": f"{type(exc).__name__}: {exc}"}


def create_pvp_battle_from_accepted_duel(request: Mapping[str, Any], *, snapshot_provider: SnapshotProvider | None = None, prepared_snapshots: Mapping[str, Any] | None = None, connection=None, activity_db_path=None) -> dict[str, Any]:
    if request.get("request_type") != "duel" or request.get("status") != "accepted":
        return {"success": False, "reason": "duel_request_not_accepted"}
    initiator = int(request["initiator_user_id"]); recipient = int(request["recipient_user_id"])
    prepared = dict(prepared_snapshots or prepare_pvp_duel_snapshots(initiator, recipient, snapshot_provider=snapshot_provider))
    if not prepared.get("success"):
        return prepared
    try:
        init_pvp_foundation(connection)
        created = create_pvp_battle(
            initiator, recipient, prepared["initiator_snapshot"], prepared["recipient_snapshot"],
            request_id=int(request["id"]), start_immediately=True, connection=connection,
        )
    except Exception as exc:
        LOGGER.exception("Persistent PvP battle creation failed for request %s", request.get("id"))
        return {"success": False, "reason": "pvp_battle_creation_failed", "error": f"{type(exc).__name__}: {exc}"}
    battle_id = int(created["battle"]["id"]); acquired = []
    for user_id in (initiator, recipient):
        result = acquire_player_activity_session(user_id, "pvp_battle", reference_id=battle_id, status="active", ttl_seconds=None, db_path=activity_db_path)
        if not result.get("success"):
            for previous in acquired:
                release_player_activity_session(previous, activity_type="pvp_battle", reference_id=battle_id, db_path=activity_db_path)
            complete_pvp_battle(battle_id, "activity_session_acquire_failed", status="cancelled", connection=connection)
            return {"success": False, "reason": "player_busy", "battle_id": battle_id}
        acquired.append(user_id)
    return {"success": True, "battle_id": battle_id, "battle": created["battle"], "participants": created["participants"]}
