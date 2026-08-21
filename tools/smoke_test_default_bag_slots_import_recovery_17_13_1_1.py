#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "game.db"
PLAYER = ROOT / "db_modules/player.py"
CONNECTION = ROOT / "db_modules/connection.py"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


before = sha256(DB)
player_source = PLAYER.read_text(encoding="utf-8")
connection_source = CONNECTION.read_text(encoding="utf-8")
ast.parse(player_source)
ast.parse(connection_source)

assert player_source.count("ROM 17.13.1.1 DEFAULT BAG SLOTS IMPORT RECOVERY") == 1
assert "from .connection import conn, cursor, DEFAULT_BAG_SLOTS" in player_source
assert "DEFAULT_BAG_SLOTS" in connection_source

from db_modules import connection, player

assert connection.DEFAULT_BAG_SLOTS == 60
assert player.DEFAULT_BAG_SLOTS == connection.DEFAULT_BAG_SLOTS
assert player.create_user.__globals__["DEFAULT_BAG_SLOTS"] == 60

# Do not call create_user here. Validate that its runtime global is resolvable.
create_source = ast.get_source_segment(player_source, next(
    node for node in ast.walk(ast.parse(player_source))
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "create_user"
)) or ""
assert "DEFAULT_BAG_SLOTS" in create_source
assert sha256(DB) == before
print("[PASS] Stage 17.13.1.1 DEFAULT_BAG_SLOTS import recovery contract")
