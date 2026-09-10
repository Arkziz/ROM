#!/usr/bin/env python3
from __future__ import annotations
import sqlite3,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import systems.notifications as n
class C:
 def __init__(self,p):self.conn=sqlite3.connect(p);self.cursor=self.conn.cursor()
def schema(c):
 c.executescript("""CREATE TABLE users(user_id INTEGER PRIMARY KEY,level INTEGER,sta INTEGER,allocated_stamina INTEGER,intelligence INTEGER,allocated_intelligence INTEGER,wis INTEGER,allocated_wisdom INTEGER,character_class TEXT,hp INTEGER,max_hp INTEGER,last_hp_regen_update TEXT,hp_full_notified INTEGER,mp INTEGER,max_mp INTEGER,last_mp_regen_update TEXT,mp_full_notified INTEGER,mp_regen_paused INTEGER);CREATE TABLE equipment_slots(user_id INTEGER,inventory_id INTEGER);CREATE TABLE inventory(id INTEGER,user_id INTEGER,item_id INTEGER,durability INTEGER,refine_level INTEGER);CREATE TABLE items(id INTEGER,bonus_sta INTEGER,bonus_int INTEGER,bonus_wis INTEGER,slot_key TEXT,rarity TEXT);CREATE TABLE inventory_runes(inventory_id INTEGER,rune_level INTEGER,rune_stat TEXT);""")
def main():
 with tempfile.TemporaryDirectory() as d:
  c=sqlite3.connect(str(Path(d)/"t.db"))
  try:
   schema(c)
   c.execute("INSERT INTO users VALUES(1,5,12,2,12,3,12,4,'mage',200,210,'',1,90,100,'',1,0)")
   c.commit()
   hp=n.get_worker_max_hp(c,1)
   mp=n.get_worker_max_mp_17_15_1(c,1)
   from data.player_hp import calculate_base_max_hp
   expected_hp=calculate_base_max_hp(5,14)
   assert hp==expected_hp,(hp,expected_hp)
   from systems.stat_system import calculate_max_mp
   expected_mp=calculate_max_mp('mage',level=5,intelligence=15,wisdom=16)
   assert mp==expected_mp,(mp,expected_mp)
   row=c.execute("SELECT hp,max_hp,mp,max_mp FROM users WHERE user_id=1").fetchone()
   assert row[0]==200 and row[1]==hp,row
   assert row[2]==90 and row[3]==100,row
  finally:
   c.close()
 print("[PASS] Stage 18.16.5d worker HP/MP allocated-stat contract")
if __name__=="__main__":main()
