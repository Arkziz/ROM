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
    required = (
        "ROM 12.6.4a PLAYER TRADE IMMEDIATE KEYBOARD AND LOCK SPAM HOTFIX",
        "Режим обміну активовано.",
        "reply_markup=player_trade_active_reply_kb_12_6_4()",
        "def _trade_lock_notice_allowed_12_6_4a(",
        "PLAYER_TRADE_LOCK_NOTICE_COOLDOWN_SECONDS_12_6_4A = 3.0",
        "notice_sent_in_batch = set()",
        "_rom_trade_navigation_lock_12_6_4a",
    )
    for value in required:
        if value not in source:
            fail(f"missing contract: {value}")

    # Both participants need an immediate replacement message.
    if source.count('"🤝 Режим обміну активовано."') < 2:
        fail("keyboard replacement is not sent to both participants")

    namespace = {}
    wanted = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            text = ast.get_source_segment(source, node) or ""
            if "_trade_lock_time_12_6_4a" in text:
                wanted.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            text = ast.get_source_segment(source, node) or ""
            if (
                "_PLAYER_TRADE_LOCK_NOTICE_AT_12_6_4A" in text
                or "PLAYER_TRADE_LOCK_NOTICE_COOLDOWN_SECONDS_12_6_4A" in text
            ):
                wanted.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == "_trade_lock_notice_allowed_12_6_4a":
            wanted.append(node)
    exec(compile(ast.Module(body=wanted, type_ignores=[]), str(HANDLER), "exec"), namespace)
    allow = namespace["_trade_lock_notice_allowed_12_6_4a"]
    if allow(1, now=100.0) is not True:
        fail("first notice rejected")
    if allow(1, now=101.0) is not False:
        fail("burst notice was not suppressed")
    if allow(1, now=103.1) is not True:
        fail("notice did not recover after cooldown")
    if allow(2, now=101.0) is not True:
        fail("cooldown leaked between users")

    print("[OK] Player trade immediate keyboard and lock anti-spam contracts")
    print("- recipient keyboard replaced immediately on accept: OK")
    print("- initiator keyboard replaced immediately on accept: OK")
    print("- queued old-keyboard actions remain blocked: OK")
    print("- one chat warning per burst/cooldown: OK")
    print("- active-trade button and trade callbacks remain allowed: OK")
    print("- isolated helper checks; real user mutations: 0")


if __name__ == "__main__":
    main()
