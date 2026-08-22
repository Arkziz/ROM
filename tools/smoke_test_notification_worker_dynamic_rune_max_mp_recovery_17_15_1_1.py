#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import hashlib
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "game.db"
SOURCE = ROOT / "systems/notifications.py"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


before = sha256(DB)
source = SOURCE.read_text(encoding="utf-8")
tree = ast.parse(source)
assert source.count("ROM 17.15.1.1 NOTIFICATION WORKER DYNAMIC RUNE MAX MP RECOVERY") == 1
assert "def get_worker_equipped_rune_int_wis_bonus_17_15_1_1" in source
assert source.count("def get_worker_max_mp_17_15_1(conn, user_id):") >= 2
assert "COALESCE(inv.durability, 100) > 0" in source
assert "rune_stat" in source and "rune_level" in source

from systems import notifications as n

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE users (user_id INTEGER PRIMARY KEY, level INTEGER, intelligence INTEGER, wis INTEGER, character_class TEXT, max_mp INTEGER)")
conn.execute("CREATE TABLE inventory (id INTEGER PRIMARY KEY, user_id INTEGER, durability INTEGER)")
conn.execute("CREATE TABLE equipment_slots (user_id INTEGER, inventory_id INTEGER)")
conn.execute("CREATE TABLE inventory_runes (inventory_id INTEGER, rune_stat TEXT, rune_level INTEGER)")
conn.execute("INSERT INTO users VALUES (1,8,67,68,'priest',0)")
conn.execute("INSERT INTO inventory VALUES (10,1,100)")
conn.execute("INSERT INTO equipment_slots VALUES (1,10)")
conn.execute("INSERT INTO inventory_runes VALUES (10,'int',2)")
conn.execute("INSERT INTO inventory_runes VALUES (10,'wis',3)")

# Base: 100 + 8*20 + 67*3 + 68*2 = 597; runes add 2*3 + 3*2 = 12.
assert n.get_worker_max_mp_17_15_1(conn, 1) == 609
assert conn.execute("SELECT max_mp FROM users WHERE user_id=1").fetchone()[0] == 609

# Broken equipment contributes no rune bonus.
conn.execute("UPDATE inventory SET durability=0 WHERE id=10")
assert n.get_worker_max_mp_17_15_1(conn, 1) == 597

# Non-mana classes are excluded.
conn.execute("UPDATE users SET character_class='warrior' WHERE user_id=1")
assert n.get_worker_max_mp_17_15_1(conn, 1) == 0
conn.close()

# The MP regen and notification functions resolve the final global max-MP helper.
regen_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "apply_mp_regen_worker_17_15_1")
regen_source = ast.get_source_segment(source, regen_node) or ""
assert "get_worker_max_mp_17_15_1(conn, user_id)" in regen_source
assert source.index("bot_instance.send_message", source.index("def notify_mp_restored_17_15_1")) < source.index("mp_full_notified=1", source.index("def notify_mp_restored_17_15_1"))
assert sha256(DB) == before
print("[PASS] Stage 17.15.1.1 rune-aware worker max-MP recovery contract")
