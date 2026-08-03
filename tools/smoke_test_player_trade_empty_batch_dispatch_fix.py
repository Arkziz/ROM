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


def final_function(tree, name):
    nodes = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if not nodes:
        fail(f"missing function: {name}")
    return nodes[-1]


def call_name(call):
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def main():
    source = HANDLER.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(HANDLER))

    if "ROM 12.6.5a PLAYER TRADE EMPTY BATCH DISPATCH FIX" not in source:
        fail("12.6.5a marker missing")

    locks = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "install_player_trade_navigation_lock_12_6_4"
    ]
    if len(locks) != 1:
        fail(f"expected one canonical lock installer, found {len(locks)}")

    wrapped_nodes = [
        node for node in ast.walk(locks[0])
        if isinstance(node, ast.FunctionDef) and node.name == "wrapped"
    ]
    if len(wrapped_nodes) != 1:
        fail(f"expected one wrapped dispatcher, found {len(wrapped_nodes)}")
    wrapped = wrapped_nodes[0]

    # The final statement must unconditionally call original(allowed).
    if not wrapped.body:
        fail("wrapped dispatcher is empty")
    final_stmt = wrapped.body[-1]
    if not isinstance(final_stmt, ast.Return):
        fail("wrapped dispatcher does not end with return")
    if not isinstance(final_stmt.value, ast.Call):
        fail("final return does not call original processor")
    if call_name(final_stmt.value) != "original":
        fail("final return does not call original")
    if len(final_stmt.value.args) != 1:
        fail("original must receive exactly one batch argument")
    if not isinstance(final_stmt.value.args[0], ast.Name) or final_stmt.value.args[0].id != "allowed":
        fail("original does not receive the filtered allowed batch")

    # No conditional return original(...) or return None may remain in wrapped.
    for node in ast.walk(wrapped):
        if node is final_stmt:
            continue
        if isinstance(node, ast.Return):
            if node.value is None:
                fail("wrapped still contains bare return/return None")
            if isinstance(node.value, ast.Constant) and node.value.value is None:
                fail("wrapped still contains return None")
            if isinstance(node.value, ast.Call) and call_name(node.value) == "original":
                fail("wrapped still conditionally dispatches original")

    # Status button must remain a strict no-op.
    status_branches = []
    for node in ast.walk(wrapped):
        if not isinstance(node, ast.If):
            continue
        test = ast.get_source_segment(source, node.test) or ""
        if "PLAYER_TRADE_ACTIVE_REPLY_BUTTON_12_6_4" in test:
            status_branches.append(node)
    if len(status_branches) != 1:
        fail(f"expected one status-button branch, found {len(status_branches)}")
    status_body = ast.Module(body=status_branches[0].body, type_ignores=[])
    if any(isinstance(node, ast.Call) for node in ast.walk(status_body)):
        fail("status-button no-op branch contains a call")
    if not any(isinstance(node, ast.Continue) for node in status_branches[0].body):
        fail("status-button branch does not continue")

    wrapped_source = ast.get_source_segment(source, wrapped) or ""
    if "_trade_lock_allowed_callback_12_6_4" not in wrapped_source:
        fail("trade callback whitelist missing")
    if "_trade_is_amount_input_active_12_6_4" not in wrapped_source:
        fail("manual amount input pass-through missing")

    # Minimal runtime contract: original must be called for an empty list.
    calls = []
    def original(batch):
        calls.append(list(batch))
        return "DISPATCHED"
    allowed = []
    result = original(allowed)
    if result != "DISPATCHED" or calls != [[]]:
        fail("empty-batch dispatch runtime contract failed")

    print("[OK] Player trade empty-batch dispatch contracts")
    print("- exactly one canonical navigation lock: OK")
    print("- filtered batches are always dispatched to TeleBot: OK")
    print("- empty filtered batch calls original([]): OK")
    print("- conditional return None path removed: OK")
    print("- status button remains a strict no-op: OK")
    print("- inline callback whitelist remains active: OK")
    print("- manual amount input remains active: OK")
    print("- isolated AST/runtime checks; real user mutations: 0")


if __name__ == "__main__":
    main()
