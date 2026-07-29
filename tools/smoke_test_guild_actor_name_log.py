#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated contracts for Guild actor-name event logs."""
from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "game.db"
GUILD_PATH = ROOT / "systems" / "guild_system.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint():
    return (
        hashlib.sha256(DB_PATH.read_bytes()).hexdigest(),
        DB_PATH.stat().st_size,
        DB_PATH.stat().st_mtime_ns,
    )


def main():
    before = fingerprint()
    source = GUILD_PATH.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(GUILD_PATH))
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in {
            "_get_guild_event_actor_name",
            "award_guild_elite_kill",
            "award_guild_contract_completion",
        }
    }
    if len(definitions) != 3:
        fail(f"required Guild functions missing: {sorted(definitions)}")

    helper_source = ast.get_source_segment(
        source, definitions["_get_guild_event_actor_name"]
    ) or ""
    elite_source = ast.get_source_segment(
        source, definitions["award_guild_elite_kill"]
    ) or ""
    contract_source = ast.get_source_segment(
        source, definitions["award_guild_contract_completion"]
    ) or ""

    if "from systems.character_system import get_character_name" not in helper_source:
        fail("actor helper does not use the canonical Character System API")
    if "user_id" in helper_source and "return str(user_id)" in helper_source:
        fail("actor helper exposes technical user_id")
    if "(переміг: {actor_name})" not in elite_source:
        fail("elite event actor suffix missing")
    if 'str(_get_guild_event_actor_name(user_id) or "").strip()' not in elite_source:
        fail("elite actor name is not normalized at the use site")
    if "(виконав: {actor_name})" not in contract_source:
        fail("contract event actor suffix missing")
    if 'str(_get_guild_event_actor_name(user_id) or "").strip()' not in contract_source:
        fail("contract actor name is not normalized at the use site")

    from systems import guild_system as guild

    originals = {
        "get_user_guild_member": guild.get_user_guild_member,
        "add_user_guild_progress": guild.add_user_guild_progress,
        "_get_guild_event_actor_name": guild._get_guild_event_actor_name,
    }
    captured = []

    try:
        guild.get_user_guild_member = lambda user_id: {
            "guild_id": 777,
            "user_id": user_id,
        }

        def fake_add(**kwargs):
            captured.append(kwargs)
            return {
                "success": True,
                "exp": kwargs.get("exp"),
                "resource": kwargs.get("resource"),
                "kills": kwargs.get("kills"),
                "contracts": kwargs.get("contracts"),
            }

        guild.add_user_guild_progress = fake_add
        guild._get_guild_event_actor_name = lambda user_id: "  Audit Hero  "

        elite_result = guild.award_guild_elite_kill(
            -90121331,
            mob={"name": "⭐️ Елітний 🔮 Audit cultist"},
        )
        contract_result = guild.award_guild_contract_completion(
            -90121332,
            contract={"target_mob_name": "🔮 Audit cultist"},
        )

        if elite_result.get("success") is not True:
            fail(f"named elite result failed: {elite_result}")
        if contract_result.get("success") is not True:
            fail(f"named contract result failed: {contract_result}")
        if len(captured) != 2:
            fail(f"named progress calls={len(captured)}, expected 2")

        elite_call, contract_call = captured
        expected_elite = (
            "Перемога над елітним мобом: ⭐️ Елітний 🔮 Audit cultist. "
            "(переміг: Audit Hero)"
        )
        expected_contract = (
            "Виконання контракту: 🔮 Audit cultist. "
            "(виконав: Audit Hero)"
        )
        if elite_call.get("reason") != expected_elite:
            fail(f"elite reason mismatch: {elite_call.get('reason')!r}")
        if contract_call.get("reason") != expected_contract:
            fail(f"contract reason mismatch: {contract_call.get('reason')!r}")
        if (elite_call.get("exp"), elite_call.get("resource"), elite_call.get("kills"), elite_call.get("contracts")) != (25, 1, 1, 0):
            fail(f"elite reward formula changed: {elite_call}")
        if (contract_call.get("exp"), contract_call.get("resource"), contract_call.get("kills"), contract_call.get("contracts")) != (50, 3, 0, 1):
            fail(f"contract reward formula changed: {contract_call}")

        captured.clear()
        guild._get_guild_event_actor_name = lambda user_id: ""
        guild.award_guild_elite_kill(
            -90121333,
            mob={"name": "⭐️ Елітний 🔮 Audit cultist"},
        )
        guild.award_guild_contract_completion(
            -90121334,
            contract={"target_mob_name": "🔮 Audit cultist"},
        )
        if len(captured) != 2:
            fail("unnamed fallback did not produce exactly two calls")
        if captured[0].get("reason") != "Перемога над елітним мобом: ⭐️ Елітний 🔮 Audit cultist.":
            fail(f"unnamed elite fallback changed: {captured[0].get('reason')!r}")
        if captured[1].get("reason") != "Виконання контракту: 🔮 Audit cultist.":
            fail(f"unnamed contract fallback changed: {captured[1].get('reason')!r}")
        if any(str(user_id) in call.get("reason", "") for user_id, call in zip((-90121333, -90121334), captured)):
            fail("technical user_id leaked into Guild reason")

    finally:
        for name, value in originals.items():
            setattr(guild, name, value)

    if before != fingerprint():
        fail("game.db changed during isolated contracts")

    print("[OK] Guild actor name log hotfix contracts")
    print("- canonical Character System name resolver: OK")
    print("- contract actor format: OK")
    print("- elite-kill actor format: OK")
    print("- surrounding whitespace normalization: OK")
    print("- unnamed-user fallback: OK")
    print("- technical user_id exposure: 0")
    print("- elite reward formula: 25 EXP / 1 resource / 1 kill")
    print("- contract reward formula: 50 EXP / 3 resource / 1 contract")
    print("- Guild progress calls per event: exactly 1")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
