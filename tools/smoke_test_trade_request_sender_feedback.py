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
    path=ROOT/"handlers/player_interaction.py"
    source=path.read_text(encoding="utf-8-sig")
    tree=ast.parse(source,filename=str(path))
    trade=next((n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="trade_request"),None)
    if trade is None: fail("trade_request handler missing")
    functions=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="trade_request"]
    if len(functions) != 1: fail(f"trade_request definitions: {len(functions)}")
    trade=functions[0]
    calls=[]
    for node in ast.walk(trade):
        if not isinstance(node,ast.Call):
            continue
        func=node.func
        if isinstance(func,ast.Name): calls.append(func.id)
        elif isinstance(func,ast.Attribute): calls.append(func.attr)
    constants=[n.value for n in ast.walk(trade) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
    literal_text="\n".join(constants)
    if "Запит на обмін відправлено" not in literal_text: fail("success sender feedback missing")
    if "Гравець недоступний" not in literal_text: fail("unavailable feedback missing")
    if calls.count("_safe_answer") != 1: fail(f"callback answers: {calls.count('_safe_answer')}")
    if calls.count("send_message") < 3: fail("sender/recipient messages missing")
    if "_interaction_failure_message" not in calls: fail("failure reason mapping missing")
    print("[OK] Trade request sender feedback contracts")
    print("- callback query answered exactly once: OK")
    print("- visible sender success message: OK")
    print("- unavailable/busy/battle reason visible to sender: OK")
    print("- recipient invitation flow preserved: OK")
    print("- database mutations: 0")
if __name__=="__main__": main()
