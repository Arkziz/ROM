#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,sqlite3,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("m043",R/"migrations/043_existing_character_attribute_point_policy.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def main():
 with tempfile.TemporaryDirectory() as d:
  c=sqlite3.connect(str(Path(d)/"t.db"))
  try:
   c.execute("""CREATE TABLE users(user_id INTEGER PRIMARY KEY,level INTEGER,
    free_attribute_points INTEGER NOT NULL,total_attribute_points_earned INTEGER NOT NULL,
    allocated_strength INTEGER NOT NULL,allocated_dexterity INTEGER NOT NULL,
    allocated_intelligence INTEGER NOT NULL,allocated_wisdom INTEGER NOT NULL,
    allocated_stamina INTEGER NOT NULL,attribute_points_migrated_at TEXT)""")
   rows=[(1,1,0,0,0,0,0,0,0,None),(2,7,3,20,2,1,1,1,12,None),(3,3,0,15,3,3,3,3,3,None),(4,5,5,20,5,5,0,0,5,"done")]
   c.executemany("INSERT INTO users VALUES(?,?,?,?,?,?,?,?,?,?)",rows);c.commit()
   result=m.up(c);c.commit()
   assert result=={"migrated":3,"compensated":1,"points_added":10,"excess_preserved":1},result
   r1=c.execute("SELECT free_attribute_points,total_attribute_points_earned,attribute_points_migrated_at FROM users WHERE user_id=1").fetchone();assert r1[0:2]==(0,0) and r1[2]
   r2=c.execute("SELECT free_attribute_points,total_attribute_points_earned FROM users WHERE user_id=2").fetchone();assert r2==(13,30),r2
   r3=c.execute("SELECT free_attribute_points,total_attribute_points_earned FROM users WHERE user_id=3").fetchone();assert r3==(0,15),r3
   r4=c.execute("SELECT free_attribute_points,total_attribute_points_earned,attribute_points_migrated_at FROM users WHERE user_id=4").fetchone();assert r4==(5,20,"done"),r4
   before=list(c.execute("SELECT * FROM users ORDER BY user_id"));second=m.up(c);c.commit();after=list(c.execute("SELECT * FROM users ORDER BY user_id"));assert second=={"migrated":0,"compensated":0,"points_added":0,"excess_preserved":0};assert before==after
  finally:c.close()
 print("[PASS] Stage 18.16.7 Policy C migration contract")
if __name__=="__main__":main()
