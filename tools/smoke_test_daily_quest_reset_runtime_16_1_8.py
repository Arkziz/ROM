from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import db_modules.quests as quests
class Result:
    def __init__(self,rows=None,row=None): self.rows=rows or []; self.row=row
    def fetchall(self): return self.rows
    def fetchone(self): return self.row
class FakeCursor:
    def __init__(self,columns,date): self.columns=columns; self.date=date; self.calls=[]
    def execute(self,sql,args=()):
        self.calls.append((" ".join(sql.split()),args))
        if sql.startswith("PRAGMA"): return Result([(i,n) for i,n in enumerate(self.columns)])
        if sql.startswith("SELECT"): return Result(row=(self.date,))
        return Result()
class FakeConn:
    def __init__(self): self.commits=0
    def commit(self): self.commits+=1
orig_cursor,orig_conn,orig_today=quests.cursor,quests.conn,quests.get_daily_today_str
try:
    quests.get_daily_today_str=lambda:"2026-08-17"
    c=FakeCursor(["user_id","daily_key","progress"],"2026-08-16"); co=FakeConn(); quests.cursor=c; quests.conn=co
    result=quests.reset_daily_quest_if_needed(1)
    assert result["mode"]=="daily_key" and result["reset"] is False and co.commits==0
    c=FakeCursor(["user_id","quest_date","progress","completed","reward_claimed"],"2026-08-16"); co=FakeConn(); quests.cursor=c; quests.conn=co
    result=quests.reset_daily_quest_if_needed(1)
    assert result["reset"] is True and co.commits==1
    assert any(call[0].startswith("UPDATE user_daily_quests") for call in c.calls)
finally:
    quests.cursor,quests.conn,quests.get_daily_today_str=orig_cursor,orig_conn,orig_today
assert callable(quests.process_daily_quest_progress_on_kill)
print("[PASS] daily quest reset runtime contract")
