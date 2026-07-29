#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated Guild contract-target logging contracts."""
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


def db_fingerprint():
    return (
        hashlib.sha256(DB_PATH.read_bytes()).hexdigest(),
        DB_PATH.stat().st_size,
        DB_PATH.stat().st_mtime_ns,
    )


def main():
    before = db_fingerprint()
    source = GUILD_PATH.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(GUILD_PATH))
    nodes = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "award_guild_contract_completion"
    ]
    if len(nodes) != 1:
        fail(f"award_guild_contract_completion definitions={len(nodes)}, expected 1")
    function_source = ast.get_source_segment(source, nodes[0]) or ""
    keys = (
        'contract.get("target_mob_name")',
        'contract.get("name")',
        'contract.get("title")',
        'contract.get("contract_name")',
    )
    for key in keys:
        if key not in function_source:
            fail(f"missing compatibility key: {key}")
    positions = [function_source.index(key) for key in keys]
    if positions != sorted(positions):
        fail("contract name lookup priority is incorrect")

    from systems import guild_system as guild

    original_member = guild.get_user_guild_member
    original_add = guild.add_user_guild_progress
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
                "exp": kwargs.get("exp", 0),
                "resource": kwargs.get("resource", 0),
                "contracts": kwargs.get("contracts", 0),
            }

        guild.add_user_guild_progress = fake_add

        cases = (
            (
                {"target_mob_name": "🧙 Audit target", "name": "Wrong fallback"},
                "Виконання контракту: 🧙 Audit target.",
                "target_mob_name",
            ),
            ({"name": "Legacy name"}, "Виконання контракту: Legacy name.", "name"),
            ({"title": "Legacy title"}, "Виконання контракту: Legacy title.", "title"),
            ({"contract_name": "Legacy contract"}, "Виконання контракту: Legacy contract.", "contract_name"),
            ("String contract", "Виконання контракту: String contract.", "string"),
            (None, "Виконання контракту: контракт.", "fallback"),
        )

        for index, (contract, expected_reason, label) in enumerate(cases):
            result = guild.award_guild_contract_completion(
                user_id=-90121310 - index,
                contract=contract,
            )
            if not result or result.get("success") is not True:
                fail(f"{label} result contract failed: {result!r}")
            actual = captured[-1]
            if actual.get("reason") != expected_reason:
                fail(
                    f"{label} reason mismatch: "
                    f"expected={expected_reason!r}, actual={actual.get('reason')!r}"
                )
            if actual.get("contracts") != 1:
                fail(f"{label} Guild contract increment is not 1")
            if actual.get("kills") != 0:
                fail(f"{label} Guild kill increment changed")

    finally:
        guild.get_user_guild_member = original_member
        guild.add_user_guild_progress = original_add

    if len(captured) != 6:
        fail(f"Guild progress calls={len(captured)}, expected 6")
    if before != db_fingerprint():
        fail("game.db changed during isolated contracts")

    print("[OK] Guild contract target log hotfix contracts")
    print("- target_mob_name priority: OK")
    print("- name/title/contract_name compatibility: OK")
    print("- string contract compatibility: OK")
    print("- generic fallback for missing data: OK")
    print("- Guild contracts increment: exactly 1")
    print("- Guild kills increment: 0")
    print("- isolated Guild progress calls: 6")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
