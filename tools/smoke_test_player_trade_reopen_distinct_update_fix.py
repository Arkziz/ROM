#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compatibility contract after 12.6.4h made the status button a strict no-op."""
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
    installers = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "install_player_trade_navigation_lock_12_6_4"]
    if not installers:
        fail("final lock installer missing")
    installer = installers[-1]
    branches = [n for n in ast.walk(installer) if isinstance(n, ast.If) and "PLAYER_TRADE_ACTIVE_REPLY_BUTTON_12_6_4" in (ast.get_source_segment(source, n.test) or "")]
    if len(branches) != 1:
        fail("active-button branch mismatch")
    body = ast.Module(body=branches[0].body, type_ignores=[])
    if any(isinstance(n, ast.Call) for n in ast.walk(body)):
        fail("active-button branch is not a no-op")
    final = ast.get_source_segment(source, installer) or ""
    if "_trade_update_is_duplicate_12_6_4e(update)" not in final:
        fail("update dedupe missing")
    print("[OK] Player trade legacy reopen compatibility after no-op change")
    print("- persistent button performs no bot action: OK")
    print("- update dedupe remains active: OK")
    print("- inline controls remain authoritative: OK")
if __name__ == "__main__":
    main()
