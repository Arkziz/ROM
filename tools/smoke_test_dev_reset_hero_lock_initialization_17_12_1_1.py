#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import hashlib
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "game.db"
SOURCE_PATH = ROOT / "db_modules/dev_compat.py"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


before = sha256(DB)
source = SOURCE_PATH.read_text(encoding="utf-8")
tree = ast.parse(source)
assert source.count("ROM 17.12.1.1 DEV RESET HERO LOCK INITIALIZATION") == 1
assert source.count("_DEV_RESET_HERO_LOCK = None") == 1
assert "def _get_dev_reset_hero_lock():" in source
assert "global _DEV_RESET_HERO_LOCK" in source
assert "threading.RLock()" in source

# The declaration must precede the getter at module level.
declaration_line = None
getter_line = None
for node in tree.body:
    if isinstance(node, ast.Assign):
        if any(isinstance(target, ast.Name) and target.id == "_DEV_RESET_HERO_LOCK" for target in node.targets):
            if isinstance(node.value, ast.Constant) and node.value.value is None:
                declaration_line = node.lineno
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_get_dev_reset_hero_lock":
        getter_line = node.lineno
assert declaration_line is not None
assert getter_line is not None
assert declaration_line < getter_line

from db_modules import dev_compat

first = dev_compat._get_dev_reset_hero_lock()
second = dev_compat._get_dev_reset_hero_lock()
assert first is second
assert type(first).__module__ == "_thread"
assert hasattr(first, "acquire") and hasattr(first, "release")
assert first.acquire(blocking=False)
first.release()
assert sha256(DB) == before
print("[PASS] Stage 17.12.1.1 DEV reset hero lock initialization contract")
