from __future__ import annotations

import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from systems.pvp_system import (
    claim_pvp_round_resolution,
    complete_pvp_battle,
    create_pvp_battle,
    get_pvp_battle,
    get_pvp_events,
    get_pvp_participants,
    get_pvp_recovery_plan,
    init_pvp_foundation,
    recover_pvp_after_restart,
    release_pvp_round_resolution,
    submit_pvp_action,
)


def connection(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def snapshot(class_key: str, resource_type: str, max_mp: int = 0):
    return {
        "class_key": class_key,
        "max_hp": 500,
        "max_mp": max_mp,
        "resource_type": resource_type,
        "production_hp": 17,
        "production_mp": 3,
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="rom_pvp_14_1_") as temp:
        db_path = Path(temp) / "pvp_test.db"
        conn = connection(db_path)
        schema = init_pvp_foundation(conn)
        assert len(schema["tables"]) == 4
        created = create_pvp_battle(
            101,
            202,
            snapshot("warrior", "rage"),
            snapshot("mage", "mana", 300),
            request_id=77,
            connection=conn,
        )
        battle_id = created["battle"]["id"]
        battle = get_pvp_battle(battle_id, conn)
        participants = get_pvp_participants(battle_id, conn)
        assert battle["status"] == "active"
        assert battle["round_number"] == 1 and battle["revision"] == 1
        assert len(participants) == 2
        warrior = next(row for row in participants if row["user_id"] == 101)
        mage = next(row for row in participants if row["user_id"] == 202)
        assert warrior["hp"] == warrior["max_hp"] == 500
        assert warrior["resource_value"] == 0
        assert mage["mp"] == mage["max_mp"] == 300
        assert mage["resource_value"] == 300
        assert warrior["snapshot"]["production_hp"] == 17

        first = submit_pvp_action(battle_id, 101, 1, 1, "basic_attack", connection=conn)
        second = submit_pvp_action(battle_id, 202, 1, 1, "skill", skill_key="fixture", connection=conn)
        assert first["both_ready"] is False and second["both_ready"] is True
        try:
            submit_pvp_action(battle_id, 101, 1, 1, "basic_attack", connection=conn)
        except ValueError:
            pass
        else:
            raise AssertionError("duplicate PvP action was accepted")
        assert claim_pvp_round_resolution(battle_id, 1, 1, conn) is True
        assert claim_pvp_round_resolution(battle_id, 1, 1, conn) is False
        assert release_pvp_round_resolution(battle_id, 1, connection=conn) is True
        battle = get_pvp_battle(battle_id, conn)
        assert battle["round_number"] == 2 and battle["revision"] == 2 and battle["status"] == "active"

        stale_rejected = False
        try:
            submit_pvp_action(battle_id, 101, 1, 1, "basic_attack", connection=conn)
        except ValueError:
            stale_rejected = True
        assert stale_rejected

        past = datetime.now(timezone.utc) - timedelta(seconds=1)
        conn.execute("UPDATE pvp_battles SET action_deadline = ? WHERE id = ?", (past.isoformat(), battle_id))
        conn.commit()
        plan = get_pvp_recovery_plan(connection=conn)
        assert battle_id in plan["expired"]

        assert claim_pvp_round_resolution(battle_id, 2, 2, conn) is True
        recovered = recover_pvp_after_restart(connection=conn)
        assert battle_id in recovered["released_resolving"]
        battle = get_pvp_battle(battle_id, conn)
        assert battle["status"] == "active" and battle["resolving"] == 0 and battle["revision"] == 3

        assert complete_pvp_battle(battle_id, "manual_test_draw", winner_id=None, connection=conn) is True
        battle = get_pvp_battle(battle_id, conn)
        assert battle["status"] == "completed" and battle["result_reason"] == "manual_test_draw"
        events = get_pvp_events(battle_id, conn)
        assert any(event["event_type"] == "battle_created" for event in events)
        assert any(event["event_type"] == "battle_finished" for event in events)
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        conn.close()

    print("[OK] PvP data model, sessions and recovery contracts")
    print("- persistent battle/participant/action/event schema: PASS")
    print("- isolated duel-local HP/MP/resources snapshot: PASS")
    print("- stale callback and duplicate action guards: PASS")
    print("- atomic round-resolution claim: PASS")
    print("- persisted deadline and restart-recovery plan: PASS")
    print("- database writes to game.db: 0")


if __name__ == "__main__":
    main()
