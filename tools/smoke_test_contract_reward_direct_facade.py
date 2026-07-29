#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post-i10c isolated contracts for the final Contract Reward facade."""
from __future__ import annotations
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db

IDS = (-90121021, -90121022, -90121023)
CAPTURE = "_base_claim_contract_reward_before_guild_reward_v1"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def columns(table):
    return [row[1] for row in db.conn.execute(f'PRAGMA table_info("{table}")').fetchall()]


def user_tables():
    result = []
    for (name,) in db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall():
        try:
            if "user_id" in columns(name):
                result.append(name)
        except Exception:
            pass
    return result


def cleanup():
    for table in [name for name in user_tables() if name != "users"]:
        for user_id in IDS:
            try:
                db.conn.execute(f'DELETE FROM "{table}" WHERE user_id=?', (user_id,))
            except Exception:
                pass
    for user_id in IDS:
        try:
            db.conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        except Exception:
            pass
    db.conn.commit()


def real_snapshot():
    cols = columns("users")
    select_list = ",".join(f'"{name}"' for name in cols)
    rows = [
        tuple(row)
        for row in db.conn.execute(
            f"SELECT {select_list} FROM users WHERE user_id>=0 ORDER BY user_id"
        ).fetchall()
    ]
    return cols, rows


def create_fixture(user_id, completed, current_kills=0, reward_exp=40):
    db.create_user(user_id)
    db.init_contract_system()
    db.conn.execute(
        "UPDATE users SET level=5, exp=0, daily_contracts_completed=0, daily_contract_date=? WHERE user_id=?",
        (db.get_today_str(), user_id),
    )
    db.conn.execute(
        """INSERT INTO user_active_contracts (
        user_id, created_date, player_level, target_mob_name, target_mob_level,
        target_min_level, target_max_level, target_kills, current_kills,
        reward_exp, completed, reward_claimed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id, db.get_today_str(), 5, "fixture_target", 5,
            1, 10, 5, current_kills, reward_exp, completed, 0,
        ),
    )
    db.conn.commit()


def state(user_id):
    user = db.conn.execute(
        "SELECT level, exp, daily_contracts_completed FROM users WHERE user_id=?",
        (user_id,),
    ).fetchone()
    contract_count = db.conn.execute(
        "SELECT COUNT(*) FROM user_active_contracts WHERE user_id=?",
        (user_id,),
    ).fetchone()[0]
    return tuple(user), int(contract_count)


def main():
    source = (ROOT / "db.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(ROOT / "db.py"))
    definitions = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "claim_contract_reward"
    ]
    if len(definitions) != 1:
        fail(f"claim_contract_reward definitions={len(definitions)}, expected 1 after i10c")

    final_source = ast.get_source_segment(source, definitions[0]) or ""
    if "systems.contract_system" not in final_source:
        fail("final db.claim_contract_reward is not a Contract System facade")
    if CAPTURE in source or hasattr(db, CAPTURE):
        fail("obsolete Contract Reward capture still exists")
    for helper in (
        "_guild_contract_reward_result_success_v1",
        "_guild_contract_reward_append_message_v1",
    ):
        if helper in source or hasattr(db, helper):
            fail(f"obsolete helper still exists: {helper}")

    before = real_snapshot()
    cleanup()
    checks = 0
    original_award = db.award_guild_contract_completion
    original_text = db.get_guild_activity_reward_text
    guild_calls = []

    try:
        missing = db.claim_contract_reward(IDS[0])
        if not isinstance(missing, dict) or missing.get("success") is not False:
            fail(f"missing-contract result failed: {missing!r}")
        checks += 1

        create_fixture(IDS[0], completed=0, current_kills=2)
        incomplete_before = state(IDS[0])
        incomplete = db.claim_contract_reward(IDS[0])
        incomplete_after = state(IDS[0])
        if incomplete.get("success") is not False or incomplete_before != incomplete_after:
            fail("incomplete contract changed state")
        checks += 1

        create_fixture(IDS[1], completed=1, current_kills=5, reward_exp=40)

        def fake_award(user_id, contract=None):
            guild_calls.append((user_id, contract))
            return {"success": True, "exp": 50, "resource": 3, "contracts": 1}

        def fake_text(result):
            return "🏰 Fixture Guild reward"

        db.award_guild_contract_completion = fake_award
        db.get_guild_activity_reward_text = fake_text

        completed = db.claim_contract_reward(IDS[1])
        completed_state = state(IDS[1])
        if completed.get("success") is not True:
            fail(f"completed result failed: {completed!r}")
        if int(completed.get("reward_exp", 0)) != 40:
            fail(f"reward_exp mismatch: {completed!r}")
        if completed_state[0][2] != 1 or completed_state[1] != 0:
            fail(f"completed state invalid: {completed_state!r}")
        if len(guild_calls) != 1 or guild_calls[0][0] != IDS[1]:
            fail(f"Guild hook calls invalid: {guild_calls!r}")
        if "Fixture Guild reward" not in str(completed.get("message") or ""):
            fail("Guild reward text was not appended")
        checks += 5

        repeat_before = state(IDS[1])
        repeat = db.claim_contract_reward(IDS[1])
        repeat_after = state(IDS[1])
        if repeat.get("success") is not False:
            fail(f"repeat claim unexpectedly succeeded: {repeat!r}")
        if repeat_before != repeat_after or len(guild_calls) != 1:
            fail("repeat reward protection failed")
        checks += 1

        # Real no-guild path: guild helper must fail safely without changing claim result.
        create_fixture(IDS[2], completed=1, current_kills=5, reward_exp=40)
        db.award_guild_contract_completion = original_award
        db.get_guild_activity_reward_text = original_text
        no_guild = db.claim_contract_reward(IDS[2])
        if no_guild.get("success") is not True or state(IDS[2])[1] != 0:
            fail(f"no-guild completed claim failed: {no_guild!r}")
        checks += 1

    finally:
        db.award_guild_contract_completion = original_award
        db.get_guild_activity_reward_text = original_text
        cleanup()

    if before != real_snapshot():
        fail("real users changed")

    print("[OK] contract reward final post-cleanup contracts")
    print(f"- contract checks: {checks}")
    print("- single public facade: OK")
    print("- obsolete capture/helpers: absent")
    print("- missing/incomplete paths: OK")
    print("- EXP and daily completion: OK")
    print("- active contract deletion: OK")
    print("- Guild hook exactly once: OK")
    print("- no-guild path: OK")
    print("- repeat reward protection: OK")
    print("- fixture cleanup: OK")
    print("- real user mutations: 0")


if __name__ == "__main__":
    main()
