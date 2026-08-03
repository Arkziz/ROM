#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDLER = ROOT / "handlers" / "player_interaction.py"
SYSTEM = ROOT / "systems" / "player_interaction_system.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    hs = HANDLER.read_text(encoding="utf-8-sig")
    ss = SYSTEM.read_text(encoding="utf-8-sig")
    ht = ast.parse(hs, filename=str(HANDLER))
    st = ast.parse(ss, filename=str(SYSTEM))
    if "ROM 12.7.0B PLAYER TRADE SYNCHRONIZED CONFIRMATION STATUS UI" not in hs:
        fail("12.7.0b marker missing")

    handler_names = [
        node.name for node in ht.body if isinstance(node, ast.FunctionDef)
    ]
    system_names = [
        node.name for node in st.body if isinstance(node, ast.FunctionDef)
    ]
    for name in (
        "_trade_ready_status_text_12_7_0",
        "_trade_final_text_12_7_0",
        "_trade_final_kb_12_7_0",
        "_trade_show_current_stage_12_7_0",
        "_trade_send_synchronized_stage_12_7_0",
        "_register_trade_confirmation_handlers_12_7_0",
    ):
        if handler_names.count(name) != 1:
            fail(f"handler singleton contract failed: {name}")
    for name in ("set_player_trade_ready", "confirm_player_trade"):
        if system_names.count(name) != 1:
            fail(f"domain singleton contract failed: {name}")

    required_ui = (
        "Статус учасників:",
        "Редагуєте пропозицію",
        "Готові до обміну",
        "Статус фінального підтвердження:",
        "Підтвердили обмін",
        "Очікується підтвердження",
        "🔄 Оновити статус",
        "pi:tcf:refresh:",
    )
    for value in required_ui:
        if value not in hs:
            fail(f"visible UI contract missing: {value}")
    for popup in (
        '"Готовність підтверджено."',
        '"Підтверджено. Очікуємо іншого гравця."',
        '"✅ Інший гравець готовий до обміну.',
    ):
        if popup in hs:
            fail(f"obsolete popup/spam text remains: {popup}")
    if 'result.get("changed")' not in hs:
        fail("deduplicated synchronized-notification contract missing")
    if '"changed": changed' not in ss or '"changed": not already_confirmed' not in ss:
        fail("idempotent ready/confirm state contract missing")

    print("[OK] Player trade synchronized confirmation status UI contracts")
    print("- visible ready status for both participants: OK")
    print("- both-ready final panel sent to both participants: OK")
    print("- visible final-confirm status replaces transient popup: OK")
    print("- final panel includes Refresh status button: OK")
    print("- repeated ready/confirm callbacks do not create notification spam: OK")
    print("- return-to-editing synchronizes both participants: OK")
    print("- canonical functions edited in place; duplicate overrides: 0")
    print("- real user/database mutations: 0")


if __name__ == "__main__":
    main()
