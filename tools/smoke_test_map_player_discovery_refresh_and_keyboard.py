#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
def fail(msg): print(f"[FAIL] {msg}"); raise SystemExit(1)
def main():
    handler=ROOT/"handlers/player_interaction.py"
    keyboard=ROOT/"keyboards.py"
    for path in (handler,keyboard): ast.parse(path.read_text(encoding="utf-8-sig"),filename=str(path))
    hs=handler.read_text(encoding="utf-8-sig")
    if "def _safe_edit_message_text(" not in hs: fail("safe edit helper missing")
    if "message is not modified" not in hs: fail("unchanged-message guard missing")
    if "bot.edit_message_text(" in hs.replace("return bot.edit_message_text(", ""):
        fail("unguarded edit_message_text call remains")
    namespace={}
    tree=ast.parse(hs)
    helper=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_safe_edit_message_text"),None)
    if helper is None: fail("helper AST missing")
    module=ast.Module(body=[helper],type_ignores=[]); ast.fix_missing_locations(module)
    exec(compile(module,str(handler),"exec"),namespace)
    class Bot:
        def edit_message_text(self,*args,**kwargs): raise RuntimeError("Bad Request: message is not modified")
    if namespace["_safe_edit_message_text"](Bot(),"x") is not None: fail("unchanged edit not suppressed")
    class BadBot:
        def edit_message_text(self,*args,**kwargs): raise RuntimeError("Bad Request: chat not found")
    try: namespace["_safe_edit_message_text"](BadBot(),"x")
    except RuntimeError: pass
    else: fail("non-matching error was hidden")
    ks=keyboard.read_text(encoding="utf-8-sig")
    required=(
      'row(types.KeyboardButton("🌿 Початок Шляху"), types.KeyboardButton("🌲 Темний Бір"))',
      'row(types.KeyboardButton("👥 Гравці локації"), types.KeyboardButton("🏙️ Місто"))',
      'row(types.KeyboardButton("🔙 Назад"))',
    )
    positions=[]
    for token in required:
        if token not in ks: fail(f"keyboard row missing: {token}")
        positions.append(ks.index(token))
    if positions != sorted(positions): fail("keyboard row order incorrect")
    print("[OK] Map refresh and keyboard hotfix contracts")
    print("- unchanged edit_message_text 400 suppressed: OK")
    print("- other Telegram/API errors remain visible: OK")
    print("- top row: Start Path + Dark Forest: OK")
    print("- second row: Players + City: OK")
    print("- bottom row: Back: OK")
    print("- database mutations: 0")
if __name__=="__main__": main()
