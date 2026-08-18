from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import db_modules.quests as q
class Res:
 def __init__(self,rows=None,row=None):self.rows=rows or [];self.row=row
 def fetchall(self):return self.rows
 def fetchone(self):return self.row
class Cur:
 def __init__(self):self.calls=[]
 def execute(self,sql,args=()):
  self.calls.append((" ".join(sql.split()),args))
  if sql.startswith("PRAGMA"):return Res(rows=[(0,"user_id"),(1,"daily_key"),(2,"progress"),(3,"target_count"),(4,"completed"),(5,"reward_claimed")])
  if sql.startswith("SELECT daily_key"):return Res(row=("2026-08-17",))
  return Res()
class Conn:
 def __init__(self):self.commits=0
 def commit(self):self.commits+=1
oc,onn,ot=q.cursor,q.conn,q.get_daily_today_str
try:
 c=Cur();co=Conn();q.cursor=c;q.conn=co;q.get_daily_today_str=lambda:"2026-08-18"
 result=q.reset_daily_quest_if_needed(7)
 assert result["reset"] is True and result["mode"]=="daily_key"
 update=next(x for x in c.calls if x[0].startswith("UPDATE user_daily_quests"))
 assert update[1]==(0,0,0,"2026-08-18",7),update
 assert co.commits==1
finally:q.cursor,q.conn,q.get_daily_today_str=oc,onn,ot
source=(ROOT/"handlers"/"daily.py").read_text(encoding="utf-8")
assert "reset_daily_quest_if_needed(user_id)" in source
import handlers.daily
print("[PASS] offline daily rollover and UI hook")
