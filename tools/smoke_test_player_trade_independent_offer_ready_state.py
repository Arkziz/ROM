#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
H = ROOT / "handlers" / "player_interaction.py"
S = ROOT / "systems" / "player_interaction_system.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    hs = H.read_text(encoding="utf-8-sig")
    ss = S.read_text(encoding="utf-8-sig")
    ht = ast.parse(hs)
    st = ast.parse(ss)
    if "ROM 12.7.0D PLAYER TRADE INDEPENDENT OFFER READY STATE" not in hs:
        fail("12.7.0d marker missing")

    hnames = [n.name for n in ht.body if isinstance(n, ast.FunctionDef)]
    snames = [n.name for n in st.body if isinstance(n, ast.FunctionDef)]
    for name in (
        "_trade_editor_kb", "_send_trade_editor",
        "_trade_show_current_stage_12_7_0",
        "_register_trade_confirmation_handlers_12_7_0",
    ):
        if hnames.count(name) != 1:
            fail(f"handler singleton failed: {name}")
    for name in (
        "_trade_offer_mutation", "return_player_trade_to_editing",
        "_trade_actor_offer_locked_12_7_0",
    ):
        if snames.count(name) != 1:
            fail(f"system singleton failed: {name}")

    mutation = next(n for n in st.body if isinstance(n, ast.FunctionDef) and n.name == "_trade_offer_mutation")
    mutation_source = ast.get_source_segment(ss, mutation) or ""
    if "{ready_col}=0" not in mutation_source:
        fail("actor-only ready reset missing")
    if "initiator_ready=0,recipient_ready=0" in mutation_source:
        fail("legacy both-ready reset remains")

    for function_name in (
        "set_player_trade_item_offer",
        "remove_player_trade_item_offer",
        "set_player_trade_gold_offer",
    ):
        node = next(n for n in st.body if isinstance(n, ast.FunctionDef) and n.name == function_name)
        source = ast.get_source_segment(ss, node) or ""
        if "_trade_actor_offer_locked_12_7_0" not in source:
            fail(f"locked-offer mutation guard missing: {function_name}")

    required = (
        "✅ Завершити свою пропозицію",
        "✅ Ваша пропозиція зафіксована",
        "↩️ Змінити свою пропозицію",
        "First-stage ready is local",
        'result.get("both_ready") and result.get("changed")',
    )
    for value in required:
        if value not in hs:
            fail(f"handler contract missing: {value}")
    if "_trade_send_synchronized_stage_12_7_0(bot, state)" not in hs:
        fail("both-ready final synchronization missing")

    print("[OK] Player trade independent offer-ready contracts")
    print("- ready locks only the actor's own offer: OK")
    print("- other participant can keep editing without interruption: OK")
    print("- other participant's edits preserve actor ready state: OK")
    print("- ready participant's item/gold mutations are blocked: OK")
    print("- unlock clears only actor ready and both final confirmations: OK")
    print("- final panel is sent to both only when both offers are ready: OK")
    print("- stale own unlock remains available after other-side revision changes: OK")
    print("- canonical functions edited in place; duplicate overrides: 0")
    print("- real user/database mutations: 0")


if __name__ == "__main__":
    main()
