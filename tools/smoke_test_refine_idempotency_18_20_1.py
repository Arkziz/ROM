#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"handlers/refine.py").read_text(encoding="utf-8-sig")
TREE=ast.parse(SOURCE)
FUNCS={n.name:n for n in TREE.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
assert "_safe_answer_refine_callback" in FUNCS
assert "build_refine_idempotency_key" in FUNCS
assert "build_refine_attempt_result_text" in FUNCS
assert 'return f"telegram:refine:{int(user_id)}:{callback_id}"' in SOURCE
assert 'call.message.message_id' not in ast.get_source_segment(SOURCE,FUNCS["build_refine_idempotency_key"])
assert SOURCE.count("_safe_answer_refine_callback(bot, call") >= 7
assert "query is too old" in SOURCE and "query id is invalid" in SOURCE
assert 'if result.get("idempotent_replay"):' in SOURCE
assert "Матеріали повторно не списувалися" in SOURCE
# Different callbacks are different attempts; duplicate delivery of one callback is stable.
ns={};module=ast.Module(body=[FUNCS["build_refine_idempotency_key"]],type_ignores=[]);ast.fix_missing_locations(module);exec(compile(module,"key_fixture","exec"),ns)
k=ns["build_refine_idempotency_key"]
assert k(7,"abc") == k(7,"abc")
assert k(7,"abc") != k(7,"def")
assert k(7,"abc") != k(8,"abc")
# Safe acknowledgement suppresses only the known expired-query 400 and re-raises other errors.
class Call: id="old"
class OldBot:
 def answer_callback_query(self,*a,**kw):raise RuntimeError("Bad Request: query is too old and response timeout expired or query ID is invalid")
class BadBot:
 def answer_callback_query(self,*a,**kw):raise RuntimeError("network down")
helper=FUNCS["_safe_answer_refine_callback"];module=ast.Module(body=[helper],type_ignores=[]);ast.fix_missing_locations(module);ns2={};exec(compile(module,"ack_fixture","exec"),ns2)
assert ns2["_safe_answer_refine_callback"](OldBot(),Call()) is False
try:ns2["_safe_answer_refine_callback"](BadBot(),Call())
except RuntimeError as e:assert "network down" in str(e)
else:raise AssertionError("unexpected suppression")
print("[PASS] Stage 18.20.1 callback-id idempotency, truthful replay and stale callback guard")
