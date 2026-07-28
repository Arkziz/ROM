#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i4c: remove Player Progression legacy captures and old db implementations."""
from __future__ import annotations
import ast
import base64
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.12i4c"
APIS = ("add_exp", "get_user_progress")
CAPTURES = tuple(f"_legacy_{name}_before_player_system_v1" for name in APIS)
POST_TEST = base64.b64decode("IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIC0qLSBjb2Rpbmc6IHV0Zi04IC0qLQoiIiJST00gOS4wLjEyaTRjOiBQbGF5ZXIgUHJvZ3Jlc3Npb24gcG9zdC1jbGVhbnVwIGNvbnRyYWN0cy4iIiIKZnJvbSBfX2Z1dHVyZV9fIGltcG9ydCBhbm5vdGF0aW9ucwppbXBvcnQgYXN0CmltcG9ydCBzeXMKZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCgpST09UID0gUGF0aChfX2ZpbGVfXykucmVzb2x2ZSgpLnBhcmVudHNbMV0KaWYgc3RyKFJPT1QpIG5vdCBpbiBzeXMucGF0aDoKICAgIHN5cy5wYXRoLmluc2VydCgwLCBzdHIoUk9PVCkpCgpBUElTID0gKCJhZGRfZXhwIiwgImdldF91c2VyX3Byb2dyZXNzIikKQ0FQVFVSRVMgPSAoCiAgICAiX2xlZ2FjeV9hZGRfZXhwX2JlZm9yZV9wbGF5ZXJfc3lzdGVtX3YxIiwKICAgICJfbGVnYWN5X2dldF91c2VyX3Byb2dyZXNzX2JlZm9yZV9wbGF5ZXJfc3lzdGVtX3YxIiwKKQpURVNUX1VTRVJfSUQgPSAtOTAxMjA0MDMKCgpkZWYgZmFpbChtZXNzYWdlKToKICAgIHByaW50KGYiW0ZBSUxdIHttZXNzYWdlfSIpCiAgICByYWlzZSBTeXN0ZW1FeGl0KDEpCgoKZGVmIHBhcnNlX2Z1bmN0aW9ucyhwYXRoKToKICAgIHRleHQgPSBwYXRoLnJlYWRfdGV4dChlbmNvZGluZz0idXRmLTgtc2lnIikKICAgIHRyZWUgPSBhc3QucGFyc2UodGV4dCwgZmlsZW5hbWU9c3RyKHBhdGgpKQogICAgcmVzdWx0ID0ge30KICAgIGZvciBub2RlIGluIHRyZWUuYm9keToKICAgICAgICBpZiBpc2luc3RhbmNlKG5vZGUsIChhc3QuRnVuY3Rpb25EZWYsIGFzdC5Bc3luY0Z1bmN0aW9uRGVmKSk6CiAgICAgICAgICAgIHJlc3VsdC5zZXRkZWZhdWx0KG5vZGUubmFtZSwgW10pLmFwcGVuZChub2RlKQogICAgcmV0dXJuIHRleHQsIHJlc3VsdAoKCmRlZiBjbGVhbnVwKGRiKToKICAgIGZvciB0YWJsZSBpbiAoImVxdWlwbWVudF9zbG90cyIsICJpbnZlbnRvcnkiLCAidXNlcl9hY3RpdmVfY29udHJhY3RzIiwgInVzZXJfZGFpbHlfcXVlc3RzIik6CiAgICAgICAgdHJ5OgogICAgICAgICAgICBkYi5jdXJzb3IuZXhlY3V0ZShmIkRFTEVURSBGUk9NIHt0YWJsZX0gV0hFUkUgdXNlcl9pZD0/IiwgKFRFU1RfVVNFUl9JRCwpKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgICAgIHBhc3MKICAgIGRiLmN1cnNvci5leGVjdXRlKCJERUxFVEUgRlJPTSB1c2VycyBXSEVSRSB1c2VyX2lkPT8iLCAoVEVTVF9VU0VSX0lELCkpCiAgICBkYi5jb25uLmNvbW1pdCgpCgoKZGVmIGluc2VydF9maXh0dXJlKGRiLCBsZXZlbCwgZXhwLCBzdGF0cz0xMCk6CiAgICBjbGVhbnVwKGRiKQogICAgZGIuY3Vyc29yLmV4ZWN1dGUoCiAgICAgICAgIiIiCiAgICAgICAgSU5TRVJUIElOVE8gdXNlcnMgKAogICAgICAgICAgICB1c2VyX2lkLCBocCwgbWF4X2hwLCBsZXZlbCwgZXhwLCBnb2xkLCBraWxscywgYmFnX3Nsb3RzLAogICAgICAgICAgICBjdXJyZW50X2xvY2F0aW9uLCBzdHIsIGRleCwgaW50ZWxsaWdlbmNlLCB3aXMsIHN0YSwgZGFpbHlfaHVudHMKICAgICAgICApIFZBTFVFUyAoPywgPywgPywgPywgPywgPywgPywgPywgPywgPywgPywgPywgPywgPywgPykKICAgICAgICAiIiIsCiAgICAgICAgKAogICAgICAgICAgICBURVNUX1VTRVJfSUQsIDE3MCwgMTcwLCBpbnQobGV2ZWwpLCBpbnQoZXhwKSwgMTIuNSwgNywgNDAsCiAgICAgICAgICAgICJzdGFydF9wYXRoIiwgaW50KHN0YXRzKSwgaW50KHN0YXRzKSwgaW50KHN0YXRzKSwgaW50KHN0YXRzKSwgaW50KHN0YXRzKSwgMywKICAgICAgICApLAogICAgKQogICAgZGIuY29ubi5jb21taXQoKQoKCmRlZiBzbmFwc2hvdChkYik6CiAgICByb3cgPSBkYi5jdXJzb3IuZXhlY3V0ZSgKICAgICAgICAiIiIKICAgICAgICBTRUxFQ1QgbGV2ZWwsIGV4cCwgc3RyLCBkZXgsIGludGVsbGlnZW5jZSwgd2lzLCBzdGEsIG1heF9ocAogICAgICAgIEZST00gdXNlcnMgV0hFUkUgdXNlcl9pZD0/CiAgICAgICAgIiIiLAogICAgICAgIChURVNUX1VTRVJfSUQsKSwKICAgICkuZmV0Y2hvbmUoKQogICAgcmV0dXJuIHR1cGxlKHJvdykgaWYgcm93IGlzIG5vdCBOb25lIGVsc2UgTm9uZQoKCmRlZiBtYWluKCk6CiAgICBkYl90ZXh0LCBkYl9kZWZzID0gcGFyc2VfZnVuY3Rpb25zKFJPT1QgLyAiZGIucHkiKQogICAgcGxheWVyX3RleHQsIHBsYXllcl9kZWZzID0gcGFyc2VfZnVuY3Rpb25zKFJPT1QgLyAic3lzdGVtcyIgLyAicGxheWVyX3N5c3RlbS5weSIpCgogICAgZm9yIG5hbWUgaW4gQVBJUzoKICAgICAgICBpZiBsZW4oZGJfZGVmcy5nZXQobmFtZSwgW10pKSAhPSAxOgogICAgICAgICAgICBmYWlsKGYiZGIucHk6IHtuYW1lfSBkZWZpbml0aW9ucz17bGVuKGRiX2RlZnMuZ2V0KG5hbWUsIFtdKSl9LCBleHBlY3RlZCAxIikKICAgICAgICBpZiBsZW4ocGxheWVyX2RlZnMuZ2V0KG5hbWUsIFtdKSkgIT0gMToKICAgICAgICAgICAgZmFpbChmInBsYXllcl9zeXN0ZW0ucHk6IHtuYW1lfSBkZWZpbml0aW9ucz17bGVuKHBsYXllcl9kZWZzLmdldChuYW1lLCBbXSkpfSwgZXhwZWN0ZWQgMSIpCiAgICAgICAgZGJfc291cmNlID0gYXN0LmdldF9zb3VyY2Vfc2VnbWVudChkYl90ZXh0LCBkYl9kZWZzW25hbWVdWzBdKSBvciAiIgogICAgICAgIHBsYXllcl9zb3VyY2UgPSBhc3QuZ2V0X3NvdXJjZV9zZWdtZW50KHBsYXllcl90ZXh0LCBwbGF5ZXJfZGVmc1tuYW1lXVswXSkgb3IgIiIKICAgICAgICBpZiAicGxheWVyX3N5c3RlbSIgbm90IGluIGRiX3NvdXJjZToKICAgICAgICAgICAgZmFpbChmImRiLntuYW1lfSBpcyBub3QgYSBwbGF5ZXJfc3lzdGVtIHdyYXBwZXIiKQogICAgICAgIGlmICJfbGVnYWN5X2Z1bmN0aW9uIiBpbiBwbGF5ZXJfc291cmNlOgogICAgICAgICAgICBmYWlsKGYicGxheWVyX3N5c3RlbS57bmFtZX0gc3RpbGwgZGVwZW5kcyBvbiBfbGVnYWN5X2Z1bmN0aW9uIikKCiAgICBmb3IgY2FwdHVyZSBpbiBDQVBUVVJFUzoKICAgICAgICBpZiBjYXB0dXJlIGluIGRiX3RleHQ6CiAgICAgICAgICAgIGZhaWwoZiJsZWdhY3kgY2FwdHVyZSB0ZXh0IHJlbWFpbnM6IHtjYXB0dXJlfSIpCgogICAgaW1wb3J0IGRiCiAgICBmcm9tIHN5c3RlbXMgaW1wb3J0IHBsYXllcl9zeXN0ZW0KCiAgICBmb3IgY2FwdHVyZSBpbiBDQVBUVVJFUzoKICAgICAgICBpZiBoYXNhdHRyKGRiLCBjYXB0dXJlKToKICAgICAgICAgICAgZmFpbChmImxlZ2FjeSBjYXB0dXJlIGlzIHN0aWxsIGV4cG9ydGVkOiB7Y2FwdHVyZX0iKQoKICAgIHJlcXVpcmVkX2tleXMgPSB7ImxldmVsIiwgImV4cCIsICJleHBfdG9fbmV4dCIsICJnb2xkIiwgImtpbGxzIiwgImRhaWx5X2h1bnRzIn0KICAgIHJlYWxfcm93cyA9IGRiLmN1cnNvci5leGVjdXRlKAogICAgICAgICJTRUxFQ1QgdXNlcl9pZCBGUk9NIHVzZXJzIFdIRVJFIHVzZXJfaWQ+PTAgT1JERVIgQlkgdXNlcl9pZCIKICAgICkuZmV0Y2hhbGwoKQogICAgcHJvZ3Jlc3NfY29tcGFyaXNvbnMgPSAwCiAgICBmb3IgKHVzZXJfaWQsKSBpbiByZWFsX3Jvd3M6CiAgICAgICAgcHVibGljID0gZGIuZ2V0X3VzZXJfcHJvZ3Jlc3ModXNlcl9pZCkKICAgICAgICBkaXJlY3QgPSBwbGF5ZXJfc3lzdGVtLmdldF91c2VyX3Byb2dyZXNzKHVzZXJfaWQpCiAgICAgICAgcHJvZ3Jlc3NfY29tcGFyaXNvbnMgKz0gMQogICAgICAgIGlmIHB1YmxpYyAhPSBkaXJlY3Q6CiAgICAgICAgICAgIGZhaWwoZiJwcm9ncmVzcyBtaXNtYXRjaCBmb3IgdXNlciB7dXNlcl9pZH0iKQogICAgICAgIGlmIG5vdCBpc2luc3RhbmNlKHB1YmxpYywgZGljdCkgb3Igbm90IHJlcXVpcmVkX2tleXMuaXNzdWJzZXQocHVibGljKToKICAgICAgICAgICAgZmFpbChmInByb2dyZXNzIGNvbnRyYWN0IGZhaWxlZCBmb3IgdXNlciB7dXNlcl9pZH0iKQoKICAgIGlmIGRiLmdldF91c2VyX3Byb2dyZXNzKC05ODc2NTQzMjEpIGlzIG5vdCBOb25lOgogICAgICAgIGZhaWwoIm1pc3NpbmctdXNlciBwcm9ncmVzcyBjb250cmFjdCBmYWlsZWQiKQoKICAgIGNhc2VzID0gW10KICAgIHRocmVzaG9sZF8xID0gaW50KGRiLmdldF9leHBfdG9fbmV4dF9sZXZlbCgxKSkKICAgIHRocmVzaG9sZF8yID0gaW50KGRiLmdldF9leHBfdG9fbmV4dF9sZXZlbCgyKSkKICAgIGNhc2VzLmFwcGVuZCgoIm5vX2xldmVsX3VwIiwgMSwgMCwgbWF4KDEsIHRocmVzaG9sZF8xIC8vIDIpLCAwKSkKICAgIGNhc2VzLmFwcGVuZCgoIm9uZV9sZXZlbF91cCIsIDEsIG1heCgwLCB0aHJlc2hvbGRfMSAtIDMpLCA1LCAxKSkKICAgIGNhc2VzLmFwcGVuZCgoIm11bHRpcGxlX2xldmVsX3VwcyIsIDEsIDAsIHRocmVzaG9sZF8xICsgdGhyZXNob2xkXzIgKyAxMSwgMikpCgogICAgdHJ5OgogICAgICAgIGZvciBsYWJlbCwgbGV2ZWwsIGV4cCwgYW1vdW50LCBleHBlY3RlZF9sZXZlbF91cHMgaW4gY2FzZXM6CiAgICAgICAgICAgIGluc2VydF9maXh0dXJlKGRiLCBsZXZlbCwgZXhwKQogICAgICAgICAgICBiZWZvcmUgPSBzbmFwc2hvdChkYikKICAgICAgICAgICAgcmVzdWx0ID0gZGIuYWRkX2V4cChURVNUX1VTRVJfSUQsIGFtb3VudCkKICAgICAgICAgICAgYWZ0ZXIgPSBzbmFwc2hvdChkYikKICAgICAgICAgICAgaWYgbm90IGlzaW5zdGFuY2UocmVzdWx0LCBkaWN0KToKICAgICAgICAgICAgICAgIGZhaWwoZiJ7bGFiZWx9OiBhZGRfZXhwIHJlc3VsdCBpcyBub3QgZGljdCIpCiAgICAgICAgICAgIGlmIGludChyZXN1bHQuZ2V0KCJsZXZlbF91cHMiLCAtMSkpICE9IGV4cGVjdGVkX2xldmVsX3VwczoKICAgICAgICAgICAgICAgIGZhaWwoZiJ7bGFiZWx9OiBsZXZlbF91cHMgbWlzbWF0Y2g6IHtyZXN1bHR9IikKICAgICAgICAgICAgaWYgYWZ0ZXIgaXMgTm9uZSBvciBiZWZvcmUgaXMgTm9uZToKICAgICAgICAgICAgICAgIGZhaWwoZiJ7bGFiZWx9OiBmaXh0dXJlIHJvdyBtaXNzaW5nIikKICAgICAgICAgICAgc3RhdF9kZWx0YSA9IHR1cGxlKGFmdGVyW2luZGV4XSAtIGJlZm9yZVtpbmRleF0gZm9yIGluZGV4IGluIHJhbmdlKDIsIDcpKQogICAgICAgICAgICBleHBlY3RlZF9kZWx0YSA9IChleHBlY3RlZF9sZXZlbF91cHMsKSAqIDUKICAgICAgICAgICAgaWYgc3RhdF9kZWx0YSAhPSBleHBlY3RlZF9kZWx0YToKICAgICAgICAgICAgICAgIGZhaWwoZiJ7bGFiZWx9OiBzdGF0IGRlbHRhIHtzdGF0X2RlbHRhfSwgZXhwZWN0ZWQge2V4cGVjdGVkX2RlbHRhfSIpCiAgICAgICAgICAgIGlmIGludChhZnRlcls3XSBvciAwKSAhPSBpbnQocGxheWVyX3N5c3RlbS5nZXRfbWF4X2hwKFRFU1RfVVNFUl9JRCkpOgogICAgICAgICAgICAgICAgZmFpbChmIntsYWJlbH06IHN0b3JlZCBtYXhfaHAgaXMgbm90IHN5bmNocm9uaXplZCIpCiAgICAgICAgICAgIGlmIGRiLmdldF91c2VyX3Byb2dyZXNzKFRFU1RfVVNFUl9JRCkgIT0gcGxheWVyX3N5c3RlbS5nZXRfdXNlcl9wcm9ncmVzcyhURVNUX1VTRVJfSUQpOgogICAgICAgICAgICAgICAgZmFpbChmIntsYWJlbH06IHB1YmxpYy9kaXJlY3QgcHJvZ3Jlc3MgbWlzbWF0Y2giKQogICAgZmluYWxseToKICAgICAgICBjbGVhbnVwKGRiKQoKICAgIGxlZnRvdmVyID0gZGIuY3Vyc29yLmV4ZWN1dGUoCiAgICAgICAgIlNFTEVDVCBDT1VOVCgqKSBGUk9NIHVzZXJzIFdIRVJFIHVzZXJfaWQ9PyIsIChURVNUX1VTRVJfSUQsKQogICAgKS5mZXRjaG9uZSgpWzBdCiAgICBpZiBpbnQobGVmdG92ZXIgb3IgMCkgIT0gMDoKICAgICAgICBmYWlsKCJpc29sYXRlZCB0ZXN0IHVzZXIgY2xlYW51cCBmYWlsZWQiKQoKICAgIHByaW50KCJbT0tdIHBsYXllciBwcm9ncmVzc2lvbiBwb3N0LWNsZWFudXAiKQogICAgcHJpbnQoIi0gcHVibGljIEFQSXM6IDIiKQogICAgcHJpbnQoIi0gZGlyZWN0IHN5c3RlbSBpbXBsZW1lbnRhdGlvbnM6IDIiKQogICAgcHJpbnQoIi0gbGVnYWN5IGNhcHR1cmVzOiAwIikKICAgIHByaW50KGYiLSBnZXRfdXNlcl9wcm9ncmVzcyBjb21wYXJpc29uczoge3Byb2dyZXNzX2NvbXBhcmlzb25zfSIpCiAgICBwcmludCgiLSBhZGRfZXhwIGNvbnRyYWN0IGNhc2VzOiAzIikKICAgIHByaW50KCItIGxldmVsLXVwIHN0YXQgaW5jcmVtZW50czogT0siKQogICAgcHJpbnQoIi0gbWF4IEhQIHN5bmNocm9uaXphdGlvbjogT0siKQogICAgcHJpbnQoIi0gbWlzc2luZy11c2VyIGNvbnRyYWN0OiBPSyIpCiAgICBwcmludCgiLSBpc29sYXRlZCB0ZXN0IHVzZXIgY2xlYW51cDogT0siKQogICAgcHJpbnQoIi0gcmVhbCB1c2VyIG11dGF0aW9uczogMCIpCgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIG1haW4oKQo=").decode("utf-8")


def fail(message):
    print(f"❌ {message}")
    raise SystemExit(1)


def find_root():
    here = Path(__file__).resolve()
    for root in (here.parent.parent, Path.cwd(), Path.cwd().parent):
        root = root.resolve()
        if (root / "db.py").is_file() and (root / "systems" / "player_system.py").is_file():
            return root
    fail("Не знайдено корінь ROM.")


def function_map(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.setdefault(node.name, []).append(node)
    return result


def main():
    root = find_root()
    db_path = root / "db.py"
    player_path = root / "systems" / "player_system.py"
    direct_test = root / "tools" / "smoke_test_player_progression_direct.py"
    audit_test = root / "tools" / "smoke_test_player_progression_legacy_audit.py"

    source = db_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(db_path))
    functions = function_map(tree)

    if all(len(functions.get(name, [])) == 1 for name in APIS) and all(c not in source for c in CAPTURES):
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано.")
        test = direct_test
        if test.is_file():
            result = subprocess.run([sys.executable, str(test)], cwd=root)
            raise SystemExit(result.returncode)
        return

    # i4b is mandatory: direct implementations must no longer call legacy.
    player_source = player_path.read_text(encoding="utf-8-sig")
    player_tree = ast.parse(player_source, filename=str(player_path))
    player_functions = function_map(player_tree)
    for name in APIS:
        nodes = player_functions.get(name, [])
        if len(nodes) != 1:
            fail(f"systems/player_system.py: {name} definitions={len(nodes)}; спочатку застосуй i4b.")
        segment = ast.get_source_segment(player_source, nodes[0]) or ""
        if "_legacy_function" in segment:
            fail(f"systems/player_system.py: {name} ще залежить від legacy; спочатку застосуй i4b.")

    for name in APIS:
        if len(functions.get(name, [])) != 2:
            fail(f"db.py: {name} definitions={len(functions.get(name, []))}, очікувалося 2.")
        final_segment = ast.get_source_segment(source, functions[name][-1]) or ""
        if "player_system" not in final_segment:
            fail(f"Фінальна db.{name} не є wrapper у player_system.")

    # Locate the dynamic player capture loop by its AST list values.
    # The concrete capture names are built with an f-string at runtime, so they
    # do not exist as literal text in db.py and must not be searched literally.
    capture_loop = None
    capture_elements = {}
    for node in tree.body:
        if not isinstance(node, ast.For):
            continue
        if not isinstance(node.target, ast.Name) or node.target.id != "_name":
            continue
        if not isinstance(node.iter, (ast.List, ast.Tuple)):
            continue
        values = {}
        for element in node.iter.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                values[element.value] = element
        segment = ast.get_source_segment(source, node) or ""
        if all(name in values for name in APIS) and "_legacy_" in segment and "before_player_system_v1" in segment:
            capture_loop = node
            capture_elements = values
            break
    if capture_loop is None:
        fail("Не знайдено player legacy capture loop за AST-структурою.")

    lines = source.splitlines(keepends=True)
    replacements = []
    # Remove only the two string entries from the capture list, preserving the loop.
    for name in APIS:
        element = capture_elements[name]
        line_index = element.lineno - 1
        line_text = lines[line_index]
        if f'"{name}"' not in line_text and f"'{name}'" not in line_text:
            fail(f"Не вдалося однозначно знайти рядок capture-list для {name}.")
        replacements.append((element.lineno, element.lineno, ""))

    for name in APIS:
        old_node = functions[name][0]
        replacements.append((old_node.lineno, old_node.end_lineno, ""))

    ordered = sorted(replacements)
    for previous, current in zip(ordered, ordered[1:]):
        if current[0] <= previous[1]:
            fail("Діапазони очищення перетинаються.")
    for start, end, replacement in sorted(replacements, reverse=True):
        lines[start - 1:end] = [replacement] if replacement else []
    updated = "".join(lines)

    updated_tree = ast.parse(updated, filename=str(db_path))
    updated_functions = function_map(updated_tree)
    for name in APIS:
        if len(updated_functions.get(name, [])) != 1:
            fail(f"Після очищення db.{name} definitions={len(updated_functions.get(name, []))}.")
    for capture in CAPTURES:
        if capture in updated:
            fail(f"Після очищення залишився {capture}.")

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_backup = backup_dir / f"db.py_{PATCH_ID}_progression_legacy_cleanup_{stamp}.bak"
    shutil.copy2(db_path, db_backup)
    test_backups = []
    for path in (direct_test, audit_test):
        if path.exists():
            backup = backup_dir / f"tools_{path.name}_{PATCH_ID}_{stamp}.bak"
            shutil.copy2(path, backup)
            test_backups.append((path, backup))

    temp_path = db_path.with_name(".db.i4c.tmp")
    try:
        temp_path.write_text(updated, encoding="utf-8")
        os.replace(temp_path, db_path)
        # Both legacy-dependent tests become one post-cleanup contract test.
        direct_test.write_text(POST_TEST, encoding="utf-8")
        audit_test.write_text(POST_TEST, encoding="utf-8")
        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(direct_test), doraise=True)
        py_compile.compile(str(audit_test), doraise=True)
        result = subprocess.run([sys.executable, str(direct_test)], cwd=root)
        if result.returncode != 0:
            raise RuntimeError(f"post-cleanup test exit code {result.returncode}")
    except Exception as exc:
        shutil.copy2(db_backup, db_path)
        restored = set()
        for path, backup in test_backups:
            shutil.copy2(backup, path)
            restored.add(path)
        for path in (direct_test, audit_test):
            if path not in restored and path.exists():
                path.unlink()
        if temp_path.exists():
            temp_path.unlink()
        fail(f"Перевірка не пройдена; файли відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ Видалено 2 старі Player Progression реалізації з db.py.")
    print("✅ Видалено 2 progression legacy refs із capture loop.")
    print("✅ Залишено wrappers db.py -> systems/player_system.py.")
    print("✅ Оновлено progression тести для post-cleanup стану.")
    print("Резервні копії:")
    print(f"   {db_backup.relative_to(root)}")
    for _path, backup in test_backups:
        print(f"   {backup.relative_to(root)}")
    print("Перевірки:")
    print("   python -m py_compile ./db.py")
    print("   python -m py_compile ./systems/player_system.py")
    print("   python ./tools/smoke_test_player_progression_direct.py")
    print("   python ./tools/smoke_test_player_contracts.py")
    print("   python ./tools/smoke_test_player_combat_stats.py")
    print("   python ./tools/smoke_test_contract_contracts.py")
    print("   python ./tools/smoke_test_rom_core.py")
    print("   python ./tools/check_imports.py")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
