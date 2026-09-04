#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import importlib.util
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "systems" / "crystal_shop_system.py"
BAG = ROOT / "systems" / "crystal_bag_expansion_system.py"
TIMED = ROOT / "systems" / "timed_exp_bonus_system.py"

source = SYSTEM.read_text(encoding="utf-8-sig")
ast.parse(source, filename=str(SYSTEM))
spec = importlib.util.spec_from_file_location("crystal_shop_stage_18_10_1", SYSTEM)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
expected = {501: 150, 602: 35, 728: 20, 502: 50}
assert {key: value["price"] for key, value in module.CRYSTAL_SHOP_CATALOG.items()} == expected
assert "BAG_EXPANSION_TIERS={60:{'target_capacity':80,'price':75},80:{'target_capacity':100,'price':150}}" in BAG.read_text(encoding="utf-8-sig")
timed_before = TIMED.read_bytes()

with tempfile.TemporaryDirectory() as folder:
    database = Path(folder) / "shop.db"
    connection = sqlite3.connect(database)
    connection.executescript("""
    PRAGMA foreign_keys=ON;
    CREATE TABLE users(user_id INTEGER PRIMARY KEY,bag_slots INTEGER);
    CREATE TABLE items(id INTEGER PRIMARY KEY,name TEXT,max_stack INTEGER);
    CREATE TABLE inventory(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,item_id INTEGER,quantity INTEGER,durability INTEGER);
    CREATE TABLE crystal_wallets(user_id INTEGER PRIMARY KEY,balance INTEGER,created_at TEXT,updated_at TEXT);
    CREATE TABLE crystal_transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,operation TEXT,amount INTEGER,reason_code TEXT,balance_before INTEGER,balance_after INTEGER,idempotency_key TEXT UNIQUE,external_reference TEXT,metadata_json TEXT,compensates_transaction_id INTEGER,created_at TEXT);
    CREATE TABLE premium_item_grants(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,item_id INTEGER,quantity INTEGER,source TEXT,idempotency_key TEXT UNIQUE,external_reference TEXT,metadata_json TEXT,created_at TEXT);
    INSERT INTO users VALUES(1,60),(2,60),(3,60),(4,60);
    INSERT INTO crystal_wallets VALUES(1,500,'',''),(2,35,'',''),(3,19,'',''),(4,500,'','');
    INSERT INTO items VALUES(501,'Sphere',10),(602,'Success',10),(728,'Perfect',999),(502,'Name',999);
    """)
    connection.commit(); connection.close()
    module.init_crystal_shop_system(database)

    preview = module.preview_crystal_shop_purchase(1,602,2,database)
    assert preview["unit_price"] == 35 and preview["total_price"] == 70
    success = module.purchase_crystal_shop_item(1,602,2,"success-rune",database)
    assert success["success"] and success["unit_price"] == 35 and success["total_price"] == 70 and success["balance"] == 430
    replay = module.purchase_crystal_shop_item(1,602,2,"success-rune",database)
    assert replay["success"] and replay["idempotent_replay"]

    exact = module.purchase_crystal_shop_item(2,602,1,"exact-balance",database)
    assert exact["success"] and exact["balance"] == 0
    insufficient = module.purchase_crystal_shop_item(3,728,1,"insufficient",database)
    assert not insufficient["success"] and insufficient["balance"] == 19
    perfect = module.purchase_crystal_shop_item(4,728,2,"perfect-two",database)
    assert perfect["success"] and perfect["unit_price"] == 20 and perfect["total_price"] == 40 and perfect["balance"] == 460

    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    rows = connection.execute("SELECT item_id,unit_price,total_price FROM crystal_shop_purchases ORDER BY id").fetchall()
    assert [(r["item_id"],r["unit_price"],r["total_price"]) for r in rows] == [(602,35,70),(602,35,35),(728,20,40)]
    assert connection.execute("SELECT COUNT(*) FROM crystal_shop_purchases WHERE idempotency_key='success-rune'").fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM crystal_transactions").fetchone()[0] == 3
    assert connection.execute("SELECT COUNT(*) FROM premium_item_grants").fetchone()[0] == 3
    assert connection.execute("SELECT COUNT(*) FROM inventory WHERE user_id=3").fetchone()[0] == 0
    assert connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    assert not list(connection.execute("PRAGMA foreign_key_check"))
    connection.close()

assert TIMED.read_bytes() == timed_before
print("PASS: catalog 150/35/20/50; atomic purchase, exact balance, insufficient balance and idempotency verified; bag 75/150 and Premium unchanged")
