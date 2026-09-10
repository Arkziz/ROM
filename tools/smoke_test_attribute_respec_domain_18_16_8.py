#!/usr/bin/env python3
import importlib.util,sqlite3,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def load(path,name):s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
mig=load(R/"migrations/044_attribute_respec_foundation.py","m044");respec=load(R/"systems/attribute_respec_system.py","respec")
class DB:
 def __init__(self,p):self.conn=sqlite3.connect(p);self.cursor=self.conn.cursor()
def main():
 with tempfile.TemporaryDirectory() as d:
  db=DB(str(Path(d)/"t.db"));c=db.cursor
  c.executescript("""PRAGMA foreign_keys=ON;CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_class TEXT,free_attribute_points INTEGER,total_attribute_points_earned INTEGER,allocated_strength INTEGER,allocated_dexterity INTEGER,allocated_intelligence INTEGER,allocated_wisdom INTEGER,allocated_stamina INTEGER,hp INTEGER,max_hp INTEGER,mp INTEGER,max_mp INTEGER);CREATE TABLE items(id INTEGER PRIMARY KEY,name TEXT,type TEXT,rarity TEXT,category TEXT,slot_key TEXT,weapon_hands INTEGER,max_stack INTEGER,sell_price REAL,item_level INTEGER,is_generated INTEGER,item_subtype TEXT);CREATE TABLE inventory(id INTEGER PRIMARY KEY,user_id INTEGER,item_id INTEGER,quantity INTEGER);INSERT INTO users VALUES(1,'rogue',3,10,2,1,1,1,2,280,300,0,0);""");mig.up(db.conn);c.execute("INSERT INTO inventory VALUES(7,1,504,1)");db.conn.commit()
  preview=respec.get_attribute_respec_preview(1,db_module=db);assert preview["returned_points"]==7 and preview["free_after"]==10
  result=respec.reset_allocated_attributes(1,7,"k1",db_module=db,max_hp_getter=lambda u:260,max_mp_getter=lambda u:0,availability_guard=lambda u,c:True)
  assert result["after"]["free_before"]==10 and result["after"]["returned_points"]==0
  assert c.execute("SELECT hp,max_hp FROM users WHERE user_id=1").fetchone()==(260,260)
  assert c.execute("SELECT COUNT(*) FROM inventory WHERE id=7").fetchone()[0]==0
  assert c.execute("SELECT COUNT(*) FROM attribute_respec_events").fetchone()[0]==1
  try:respec.reset_allocated_attributes(1,7,"k1",db_module=db)
  except respec.RespecAlreadyProcessed:pass
  else:raise AssertionError("duplicate confirmation accepted")
  db.conn.close()
 print("[PASS] Stage 18.16.8 canonical respec domain contract")
if __name__=="__main__":main()
