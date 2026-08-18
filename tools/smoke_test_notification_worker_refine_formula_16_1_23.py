from __future__ import annotations
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import systems.notifications as n
c=sqlite3.connect(":memory:")
c.executescript("""
CREATE TABLE users(user_id INTEGER PRIMARY KEY,level INTEGER,sta INTEGER,max_hp INTEGER);
CREATE TABLE items(id INTEGER PRIMARY KEY,slot_key TEXT,category TEXT,bonus_sta INTEGER,rarity TEXT);
CREATE TABLE inventory(id INTEGER PRIMARY KEY,user_id INTEGER,item_id INTEGER,durability INTEGER,refine_level INTEGER);
CREATE TABLE equipment_slots(user_id INTEGER,slot_key TEXT,inventory_id INTEGER);
CREATE TABLE inventory_runes(id INTEGER PRIMARY KEY,inventory_id INTEGER,rune_stat TEXT,rune_level INTEGER);
INSERT INTO users VALUES(1,8,17,0);
INSERT INTO items VALUES(10,'ring','equipment',9,'uncommon');
INSERT INTO items VALUES(11,'chest','equipment',0,'rare');
INSERT INTO inventory VALUES(20,1,10,100,0);
INSERT INTO inventory VALUES(21,1,11,100,5);
INSERT INTO equipment_slots VALUES(1,'ring',20);
INSERT INTO equipment_slots VALUES(1,'chest',21);
INSERT INTO inventory_runes VALUES(30,20,'sta',3);
""")
assert n.get_worker_equipped_rune_sta_bonus_v2(c,1)==3
assert n.get_worker_armor_refine_hp_bonus_percent_v1(c,1)==3.6
# 100 + 8*20 + (17 base + 9 item + 3 rune)*5 = 405; rare +5 = 3.6%.
assert round(405*1.036)==420
assert n.get_worker_max_hp(c,1)==420
c.execute("UPDATE inventory SET durability=0 WHERE id=21")
assert n.get_worker_armor_refine_hp_bonus_percent_v1(c,1)==0.0
print("[PASS] exact worker refine formula returns 420")
