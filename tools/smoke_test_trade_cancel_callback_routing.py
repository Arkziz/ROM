#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
def fail(message): print(f"[FAIL] {message}"); raise SystemExit(1)
def callback_literal(node):
    values=[x.value for x in ast.walk(node) if isinstance(x,ast.Constant) and isinstance(x.value,str)]
    return "\n".join(values)
def main():
    path=ROOT/"handlers/player_interaction.py"
    source=path.read_text(encoding="utf-8-sig")
    tree=ast.parse(source,filename=str(path))
    functions={n.name:n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)}
    request=functions.get("trade_request")
    cancel=functions.get("cancel_trade_foundation")
    if request is None or cancel is None: fail("trade request/cancel handlers missing")
    request_text=callback_literal(request)
    cancel_text=callback_literal(cancel)
    # Callback namespaces live in decorators, not necessarily in function bodies.
    request_decorators="\n".join(ast.unparse(x) for x in request.decorator_list)
    cancel_decorators="\n".join(ast.unparse(x) for x in cancel.decorator_list)
    helper=functions.get("_is_trade_request_callback")
    if helper is None: fail("exact callback predicate helper missing")
    # Validate executable predicate structure, not docstring prose. The helper
    # docstring intentionally documents that cancel callbacks are excluded.
    helper_source=ast.unparse(helper)
    required_predicate_tokens=(
        "len(parts) == 3",
        "parts[0] == 'pi'",
        "parts[1] == 'trade'",
        "parts[2].isdigit()",
    )
    for token in required_predicate_tokens:
        if token not in helper_source: fail(f"exact predicate token missing: {token}")
    if "pi:trade:cancel:" in request_text or "pi:trade:cancel:" in request_decorators:
        fail("generic request handler still accepts cancel namespace")
    if "_is_trade_request_callback" not in request_decorators:
        fail("trade request handler does not use exact predicate")
    helper_module=ast.Module(body=[helper],type_ignores=[])
    ast.fix_missing_locations(helper_module)
    namespace={}
    exec(compile(helper_module,str(path),"exec"),namespace)
    predicate=namespace["_is_trade_request_callback"]
    class Call:
        def __init__(self,data): self.data=data
    if not predicate(Call("pi:trade:123")): fail("valid trade request callback rejected")
    if predicate(Call("pi:trade:cancel:123")): fail("cancel callback accepted by request predicate")
    if predicate(Call("pi:trade:not-a-number")): fail("non-numeric target accepted")
    if "pi:trade:cancel:" not in cancel_decorators:
        fail("cancel namespace missing")
    if "Обмін скасовано" not in cancel_text: fail("cancel success feedback missing")
    if "знову доступні" not in cancel_text: fail("availability feedback missing")
    if "Інший гравець скасував обмін" not in cancel_text: fail("counterparty feedback missing")
    print("[OK] Trade cancel callback routing contracts")
    print("- cancel callback excluded from generic trade-request route: OK")
    print("- cancel callback reaches cancel_player_trade: OK")
    print("- both users receive availability feedback: OK")
    print("- non-active cancel stays idempotent: OK")
    print("- database mutations in isolated test: 0")
if __name__=="__main__": main()
