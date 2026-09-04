#!/usr/bin/env python3
from pathlib import Path
import os,sqlite3,sys,tempfile
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.inactivity_reminder_system import *
p=Path(tempfile.mkdtemp())/'t.db';c=sqlite3.connect(p);c.execute("PRAGMA foreign_keys=ON");c.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT,character_class TEXT,last_activity_at TEXT)");now=datetime(2026,9,4,12,0,tzinfo=timezone.utc);old=(now-timedelta(days=7)).isoformat();before=(now-timedelta(days=7)+timedelta(seconds=1)).isoformat();c.executemany("INSERT INTO users VALUES(?,?,?,?)",[(1,'A','warrior',old),(2,'B','mage',before),(3,'','mage',old)]);c.commit();c.close();init_inactivity_reminder_system(p)
assert [r['user_id'] for r in get_eligible_inactivity_users(now,p)]==[1]
class Bot:
 def __init__(self,fail=None):self.sent=[];self.fail=fail
 def send_message(self,uid,text):
  if self.fail:raise RuntimeError(self.fail)
  self.sent.append((uid,text))
b=Bot();r=process_inactivity_reminders(b,now,p);assert r['sent']==1 and len(b.sent)==1
r=process_inactivity_reminders(b,now,p);assert r['sent']==0 and len(b.sent)==1
c=sqlite3.connect(p);c.execute("UPDATE users SET last_activity_at=? WHERE user_id=1",((now-timedelta(days=8)).isoformat(),));c.commit();c.close();r=process_inactivity_reminders(b,now,p);assert r['sent']==1 and len(b.sent)==2
c=sqlite3.connect(p);c.execute("INSERT INTO users VALUES(4,'C','scout',?)",(old,));c.commit();c.close();r=process_inactivity_reminders(Bot('bot was blocked by the user'),now,p);assert r['blocked']==1
c=sqlite3.connect(p);rows=c.execute("SELECT user_id,delivery_status FROM inactivity_reminders ORDER BY id").fetchall();c.close();assert rows==[(1,'sent'),(1,'sent'),(4,'blocked')]
assert len(INACTIVITY_REMINDER_TEXT)<=4096 and '/start' in INACTIVITY_REMINDER_TEXT
print('PASS: 7-day boundary, one attempt per cycle, restart persistence, new cycle and blocked status')
