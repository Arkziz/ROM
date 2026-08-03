#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDLER = ROOT / "handlers" / "player_interaction.py"

def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)

def main():
    source = HANDLER.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(HANDLER))
    if "ROM 12.6.4h PLAYER TRADE STATUS BUTTON NOOP" not in source:
        fail("hotfix marker missing")

    installers = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "install_player_trade_navigation_lock_12_6_4"
    ]
    if not installers:
        fail("final lock installer missing")
    installer = installers[-1]
    active_branches = []
    for node in ast.walk(installer):
        if not isinstance(node, ast.If):
            continue
        test = ast.get_source_segment(source, node.test) or ""
        if "PLAYER_TRADE_ACTIVE_REPLY_BUTTON_12_6_4" in test:
            active_branches.append(node)
    if len(active_branches) != 1:
        fail(f"expected one active-button branch, found {len(active_branches)}")

    branch = active_branches[0]
    branch_module = ast.Module(body=branch.body, type_ignores=[])
    calls = [node for node in ast.walk(branch_module) if isinstance(node, ast.Call)]
    if calls:
        call_names = []
        for call in calls:
            if isinstance(call.func, ast.Name):
                call_names.append(call.func.id)
            elif isinstance(call.func, ast.Attribute):
                call_names.append(call.func.attr)
        fail(f"active-button no-op branch contains calls: {call_names}")
    if not any(isinstance(node, ast.Continue) for node in branch.body):
        fail("active-button branch does not terminate with continue")

    installer_source = ast.get_source_segment(source, installer) or ""
    for forbidden in (
        "_trade_status_button_stub_12_6_4g",
        "_trade_reopen_directly_12_6_4d",
    ):
        if forbidden in installer_source:
            fail(f"obsolete status action remains in final lock: {forbidden}")
    if "_trade_update_is_duplicate_12_6_4e(update)" not in installer_source:
        fail("update-id dedupe missing")
    if "_trade_is_amount_input_active_12_6_4(user_id)" not in installer_source:
        fail("amount-input pass-through missing")
    if "_trade_lock_allowed_callback_12_6_4" not in installer_source:
        fail("trade callback whitelist missing")

    print("[OK] Player trade status-button no-op contracts")
    print("- persistent button update is consumed without API calls: OK")
    print("- editor is not refreshed or duplicated: OK")
    print("- no cooldown or trade state is changed by the button: OK")
    print("- inline Refresh and other trade callbacks remain allowed: OK")
    print("- manual amount input remains allowed: OK")
    print("- isolated AST checks; real user mutations: 0")

if __name__ == "__main__":
    main()
